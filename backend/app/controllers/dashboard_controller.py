from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from datetime import datetime, timedelta
from sqlalchemy import func
import numpy as np
from collections import Counter

from app.db.models import User, DiagnosisSession, VoiceMetrics
from app.services.voice_analysis_service import VoiceAnalysisService
from app.schemas.voice import VoiceHistoryResponse, VoiceStatsResponse

class DashboardController:
    def __init__(self, db: Session):
        self.voice_analysis_service = VoiceAnalysisService(db)

    async def get_user_statistics(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """获取用户统计数据"""
        # 获取诊断会话总数
        total_sessions = db.query(DiagnosisSession).filter(
            DiagnosisSession.user_id == user_id
        ).count()
        
        # 获取最近的诊断会话
        recent_sessions = db.query(DiagnosisSession).filter(
            DiagnosisSession.user_id == user_id
        ).order_by(DiagnosisSession.created_at.desc()).limit(5).all()
        
        # 获取平均预测分数
        avg_prediction = db.query(
            func.avg(VoiceMetrics.model_prediction)
        ).join(
            DiagnosisSession
        ).filter(
            DiagnosisSession.user_id == user_id
        ).scalar() or 0
        
        return {
            "total_sessions": total_sessions,
            "recent_sessions": [
                {
                    "id": session.id,
                    "created_at": session.created_at,
                    "prediction": session.metrics.model_prediction if session.metrics else None
                }
                for session in recent_sessions
            ],
            "average_prediction": round(avg_prediction, 2)
        }

    async def get_session_history(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取诊断历史记录"""
        sessions = db.query(DiagnosisSession).filter(
            DiagnosisSession.user_id == user_id
        ).order_by(
            DiagnosisSession.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        result = []
        for session in sessions:
            # 检查voice_metrics是否为列表
            if hasattr(session, 'voice_metrics'):
                if isinstance(session.voice_metrics, list):
                    # 如果是列表，取第一个元素（如果存在）
                    vm = session.voice_metrics[0] if session.voice_metrics else None
                    prediction = vm.model_prediction if vm else None
                    confidence = vm.model_confidence if vm else None
                else:
                    # 如果不是列表，直接使用
                    prediction = session.voice_metrics.model_prediction if session.voice_metrics else None
                    confidence = session.voice_metrics.model_confidence if session.voice_metrics else None
            else:
                # 如果没有voice_metrics属性
                prediction = None
                confidence = None
                
            result.append({
                "id": session.id,
                "created_at": session.created_at,
                "prediction": prediction,
                "confidence": confidence,
                "llm_suggestion": session.diagnosis_suggestion if hasattr(session, 'diagnosis_suggestion') else None
            })
        
        return result

    async def get_trend_analysis(
        self,
        db: Session,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取趋势分析数据"""
        # 获取指定天数内的诊断记录
        start_date = datetime.now() - timedelta(days=days)
        sessions = db.query(DiagnosisSession).filter(
            DiagnosisSession.user_id == user_id,
            DiagnosisSession.created_at >= start_date
        ).order_by(DiagnosisSession.created_at).all()
        
        # 按日期分组统计数据
        daily_stats = {}
        for session in sessions:
            date = session.created_at.date()
            if date not in daily_stats:
                daily_stats[date] = {
                    "count": 0,
                    "predictions": []
                }
            daily_stats[date]["count"] += 1
            if session.metrics:
                daily_stats[date]["predictions"].append(
                    session.metrics.model_prediction
                )
        
        # 计算每日平均值
        trend_data = []
        for date, stats in sorted(daily_stats.items()):
            avg_prediction = (
                sum(stats["predictions"]) / len(stats["predictions"])
                if stats["predictions"]
                else 0
            )
            trend_data.append({
                "date": date.isoformat(),
                "count": stats["count"],
                "average_prediction": round(avg_prediction, 2)
            })
        
        return {
            "trend_data": trend_data,
            "total_sessions": sum(stats["count"] for stats in daily_stats.values()),
            "average_prediction": round(
                sum(
                    sum(stats["predictions"]) / len(stats["predictions"])
                    for stats in daily_stats.values()
                    if stats["predictions"]
                ) / len(daily_stats),
                2
            ) if daily_stats else 0
        }

    async def get_spectrum_analysis(
        self,
        db: Session,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取频谱分析数据"""
        try:
            # 处理日期范围
            query_filters = [DiagnosisSession.user_id == user_id]
            
            if start_date:
                try:
                    start = datetime.strptime(start_date, "%Y-%m-%d").date()
                    query_filters.append(func.date(DiagnosisSession.created_at) >= start)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="开始日期格式无效，请使用YYYY-MM-DD格式"
                    )
            
            if end_date:
                try:
                    end = datetime.strptime(end_date, "%Y-%m-%d").date()
                    query_filters.append(func.date(DiagnosisSession.created_at) <= end)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="结束日期格式无效，请使用YYYY-MM-DD格式"
                    )
            
            # 查询所有符合条件的会话
            sessions = db.query(DiagnosisSession).filter(
                *query_filters
            ).all()
            
            # 收集所有会话ID
            session_ids = [session.id for session in sessions]
            
            # 处理语音指标数据
            voice_metrics_list = db.query(VoiceMetrics).filter(
                VoiceMetrics.session_id.in_(session_ids)
            ).all()
            
            if not voice_metrics_list:
                return {
                    "message": "未找到符合条件的数据",
                    "data": {
                        "f0_distribution": [],
                        "hnr_distribution": [],
                        "spectrogram_data": []
                    }
                }
            
            # 计算各项指标的统计分布
            metrics_data = {
                "f0_values": [metrics.f0 for metrics in voice_metrics_list if metrics.f0 is not None],
                "hnr_values": [metrics.hnr for metrics in voice_metrics_list if metrics.hnr is not None],
                "ste_values": [metrics.short_time_energy for metrics in voice_metrics_list if metrics.short_time_energy is not None],
                "zcr_values": [metrics.zero_crossing_rate for metrics in voice_metrics_list if metrics.zero_crossing_rate is not None],
                "spectral_centroid_values": [metrics.spectral_centroid for metrics in voice_metrics_list if metrics.spectral_centroid is not None]
            }
            
            # 计算各值的分布
            f0_distribution = self._get_distribution_data(metrics_data["f0_values"], 10, "基频 (Hz)")
            hnr_distribution = self._get_distribution_data(metrics_data["hnr_values"], 10, "谐噪比 (dB)")
            ste_distribution = self._get_distribution_data(metrics_data["ste_values"], 10, "短时能量")
            zcr_distribution = self._get_distribution_data(metrics_data["zcr_values"], 10, "过零率")
            sc_distribution = self._get_distribution_data(metrics_data["spectral_centroid_values"], 10, "频谱质心 (Hz)")
            
            # 统计不同健康状态的数量
            health_status_count = Counter([m.model_prediction for m in voice_metrics_list if m.model_prediction])
            
            return {
                "total_sessions": len(session_ids),
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "distributions": {
                    "f0": f0_distribution,
                    "hnr": hnr_distribution,
                    "short_time_energy": ste_distribution,
                    "zero_crossing_rate": zcr_distribution,
                    "spectral_centroid": sc_distribution
                },
                "health_status": {status: count for status, count in health_status_count.items()},
                "average_metrics": {
                    "f0": np.mean(metrics_data["f0_values"]) if metrics_data["f0_values"] else None,
                    "hnr": np.mean(metrics_data["hnr_values"]) if metrics_data["hnr_values"] else None,
                    "short_time_energy": np.mean(metrics_data["ste_values"]) if metrics_data["ste_values"] else None
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取频谱分析数据失败: {str(e)}"
            )

    async def get_clustering_analysis(
        self,
        db: Session,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取聚类分析数据"""
        try:
            # 处理日期范围
            query_filters = [DiagnosisSession.user_id == user_id]
            
            if start_date:
                try:
                    start = datetime.strptime(start_date, "%Y-%m-%d").date()
                    query_filters.append(func.date(DiagnosisSession.created_at) >= start)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="开始日期格式无效，请使用YYYY-MM-DD格式"
                    )
            
            if end_date:
                try:
                    end = datetime.strptime(end_date, "%Y-%m-%d").date()
                    query_filters.append(func.date(DiagnosisSession.created_at) <= end)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="结束日期格式无效，请使用YYYY-MM-DD格式"
                    )
            
            # 查询所有符合条件的会话
            sessions = db.query(DiagnosisSession).filter(
                *query_filters
            ).all()
            
            # 收集所有会话ID
            session_ids = [session.id for session in sessions]
            
            # 处理语音指标数据
            voice_metrics_list = db.query(VoiceMetrics).filter(
                VoiceMetrics.session_id.in_(session_ids)
            ).all()
            
            if not voice_metrics_list:
                return {
                    "message": "未找到符合条件的数据",
                    "clusters": [],
                    "scatter_data": []
                }
            
            # 准备聚类数据
            clusters = []
            cluster_data = {}
            
            for metrics in voice_metrics_list:
                if metrics.model_prediction:
                    if metrics.model_prediction not in cluster_data:
                        cluster_data[metrics.model_prediction] = {
                            "f0": [],
                            "hnr": [],
                            "session_ids": []
                        }
                    
                    if metrics.f0 is not None and metrics.hnr is not None:
                        cluster_data[metrics.model_prediction]["f0"].append(metrics.f0)
                        cluster_data[metrics.model_prediction]["hnr"].append(metrics.hnr)
                        cluster_data[metrics.model_prediction]["session_ids"].append(metrics.session_id)
            
            # 计算每个聚类的中心点和统计信息
            for status, data in cluster_data.items():
                if data["f0"] and data["hnr"]:
                    clusters.append({
                        "status": status,
                        "center": {
                            "f0": np.mean(data["f0"]),
                            "hnr": np.mean(data["hnr"])
                        },
                        "count": len(data["f0"]),
                        "std": {
                            "f0": np.std(data["f0"]),
                            "hnr": np.std(data["hnr"])
                        }
                    })
            
            # 准备散点图数据
            scatter_data = []
            for metrics in voice_metrics_list:
                if metrics.f0 is not None and metrics.hnr is not None:
                    scatter_data.append({
                        "session_id": metrics.session_id,
                        "f0": metrics.f0,
                        "hnr": metrics.hnr,
                        "status": metrics.model_prediction
                    })
            
            return {
                "clusters": clusters,
                "scatter_data": scatter_data,
                "total_points": len(scatter_data)
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取聚类分析数据失败: {str(e)}"
            )

    def _get_distribution_data(
        self,
        values: List[float],
        num_bins: int,
        label: str
    ) -> Dict[str, Any]:
        """计算数值分布数据"""
        if not values:
            return {
                "label": label,
                "bins": [],
                "counts": []
            }
        
        hist, bin_edges = np.histogram(values, bins=num_bins)
        return {
            "label": label,
            "bins": bin_edges.tolist(),
            "counts": hist.tolist()
        }

    async def get_latest_analysis(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """获取最新的语音分析结果"""
        latest_metrics = db.query(VoiceMetrics).filter(
            VoiceMetrics.user_id == user_id
        ).order_by(VoiceMetrics.created_at.desc()).first()
        
        if not latest_metrics:
            return None
            
        return {
            "metrics": {
                "rms": latest_metrics.rms,
                "zcr": latest_metrics.zcr,
                "model_prediction": latest_metrics.model_prediction,
                "model_confidence": latest_metrics.model_confidence
            },
            "created_at": latest_metrics.created_at
        }

    async def get_historical_metrics(
        self,
        db: Session,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取历史语音指标数据"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        metrics = db.query(VoiceMetrics).filter(
            VoiceMetrics.user_id == user_id,
            VoiceMetrics.created_at >= start_date
        ).order_by(VoiceMetrics.created_at.asc()).all()
        
        return {
            "dates": [m.created_at.strftime("%Y-%m-%d") for m in metrics],
            "rms_values": [m.rms for m in metrics],
            "zcr_values": [m.zcr for m in metrics],
            "confidence_values": [m.model_confidence for m in metrics],
            "predictions": [m.model_prediction for m in metrics]
        }

    async def get_voice_history(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> VoiceHistoryResponse:
        """获取语音分析历史记录"""
        total = db.query(VoiceMetrics).filter(
            VoiceMetrics.user_id == user_id
        ).count()
        
        records = db.query(VoiceMetrics).filter(
            VoiceMetrics.user_id == user_id
        ).order_by(
            VoiceMetrics.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        history = []
        for record in records:
            session = db.query(DiagnosisSession).filter(
                DiagnosisSession.metrics_id == record.id
            ).first()
            
            history_record = {
                "id": record.id,
                "created_at": record.created_at,
                "f0": record.f0,
                "hnr": record.hnr,
                "short_time_energy": record.short_time_energy,
                "zero_crossing_rate": record.zcr,
                "spectral_centroid": record.spectral_centroid,
                "model_prediction": record.model_prediction,
                "model_confidence": record.model_confidence,
                "session_id": session.id if session else None
            }
            history.append(history_record)
        
        return VoiceHistoryResponse(
            total=total,
            skip=skip,
            limit=limit,
            records=history
        )

    async def get_voice_stats(
        self,
        db: Session,
        user_id: int
    ) -> VoiceStatsResponse:
        """获取语音分析统计数据"""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # 总分析次数
        total_analyses = db.query(VoiceMetrics).filter(
            VoiceMetrics.user_id == user_id
        ).count()
        
        # 最近30天分析次数
        recent_analyses = db.query(VoiceMetrics).filter(
            VoiceMetrics.user_id == user_id,
            VoiceMetrics.created_at >= thirty_days_ago
        ).count()
        
        # 预测结果分布
        prediction_distribution = db.query(
            VoiceMetrics.model_prediction,
            func.count(VoiceMetrics.id)
        ).filter(
            VoiceMetrics.user_id == user_id,
            VoiceMetrics.model_prediction.isnot(None)
        ).group_by(
            VoiceMetrics.model_prediction
        ).all()
        
        # 平均置信度
        avg_confidence = db.query(
            func.avg(VoiceMetrics.model_confidence)
        ).filter(
            VoiceMetrics.user_id == user_id,
            VoiceMetrics.model_confidence.isnot(None)
        ).scalar() or 0
        
        return VoiceStatsResponse(
            total_analyses=total_analyses,
            recent_analyses=recent_analyses,
            prediction_distribution=dict(prediction_distribution),
            avg_confidence=float(avg_confidence)
        ) 