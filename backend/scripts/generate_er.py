"""
执行:  python scripts/generate_er.py
输出:  er_diagram.png  (标准ER图 - 实体用矩形，属性用椭圆，关系用菱形)
"""
import os
import pydot

# 设置输出路径为项目根目录
output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'er_diagram.png'))

# 创建图表
graph = pydot.Dot("ER Diagram", graph_type="graph", rankdir="TB", splines="true", overlap="false")

# 实体节点 - 矩形
user_entity = pydot.Node("User", shape="box", style="filled", fillcolor="#E0E0E0", pos="0,0!")
metrics_entity = pydot.Node("VoiceMetrics", shape="box", style="filled", fillcolor="#E0E0E0", pos="4,4!")
diagnosis_entity = pydot.Node("DiagnosisSession", shape="box", style="filled", fillcolor="#E0E0E0", pos="8,0!")

# 关系节点 - 菱形
user_has_metrics = pydot.Node("uploads", shape="diamond", style="filled", fillcolor="#FFD700", pos="2,2!")
metrics_has_diagnosis = pydot.Node("referenced_by", shape="diamond", style="filled", fillcolor="#FFD700", pos="6,2!")
user_has_sessions = pydot.Node("creates", shape="diamond", style="filled", fillcolor="#FFD700", pos="4,0!")

# User 实体的属性 - 椭圆
user_id = pydot.Node("user_id", shape="ellipse", style="filled", fillcolor="#FFFFFF", fontsize="10", pos="-1.5,1!")
username = pydot.Node("username", shape="ellipse", style="filled", fillcolor="#FFFFFF", fontsize="10", pos="-1.5,0!")
email = pydot.Node("email", shape="ellipse", style="filled", fillcolor="#FFFFFF", fontsize="10", pos="-1.5,-1!")
hashed_password = pydot.Node("hashed_password", shape="ellipse", style="filled", fillcolor="#FFFFFF", fontsize="10", pos="-1.5,-2!")

# VoiceMetrics 实体的属性 - 椭圆（选择一些关键属性，不全部显示）
metrics_id = pydot.Node("metrics_id", shape="ellipse", style="filled", fillcolor="#FFFFFF", fontsize="10", pos="2.5,5.5!")
voice_file_path = pydot.Node("voice_file_path", shape="ellipse", style="filled", fillcolor="#FFFFFF", fontsize="10", pos="3.5,5.5!")
mfcc = pydot.Node("mfcc", shape="ellipse", style="filled", fillcolor="#FFFFFF", fontsize="10", pos="4.5,5.5!")
delta = pydot.Node("delta", shape="ellipse", style="filled", fillcolor="#FFFFFF", fontsize="10", pos="5.5,5.5!")
model_prediction = pydot.Node("model_prediction", shape="ellipse", style="filled", fillcolor="#FFFFFF", fontsize="10", pos="3,6!")
model_confidence = pydot.Node("model_confidence", shape="ellipse", style="filled", fillcolor="#FFFFFF", fontsize="10", pos="5,6!")

# DiagnosisSession 实体的属性 - 椭圆
session_id = pydot.Node("session_id", shape="ellipse", style="filled", fillcolor="#FFFFFF", fontsize="10", pos="9.5,1!")
session_time = pydot.Node("session_time", shape="ellipse", style="filled", fillcolor="#FFFFFF", fontsize="10", pos="9.5,0!")
llm_suggestion = pydot.Node("llm_suggestion", shape="ellipse", style="filled", fillcolor="#FFF0F0", fontsize="10", pos="9.5,-1!")
llm_processed_at = pydot.Node("llm_processed_at", shape="ellipse", style="filled", fillcolor="#FFFFFF", fontsize="10", pos="9.5,-2!")

# 添加所有节点到图表
graph.add_node(user_entity)
graph.add_node(metrics_entity)
graph.add_node(diagnosis_entity)

graph.add_node(user_has_metrics)
graph.add_node(metrics_has_diagnosis)
graph.add_node(user_has_sessions)

# 添加User属性
graph.add_node(user_id)
graph.add_node(username)
graph.add_node(email)
graph.add_node(hashed_password)

# 添加VoiceMetrics属性
graph.add_node(metrics_id)
graph.add_node(voice_file_path)
graph.add_node(mfcc)
graph.add_node(delta)
graph.add_node(model_prediction)
graph.add_node(model_confidence)

# 添加DiagnosisSession属性
graph.add_node(session_id)
graph.add_node(session_time)
graph.add_node(llm_suggestion)
graph.add_node(llm_processed_at)

# 连接实体和关系
graph.add_edge(pydot.Edge(user_entity, user_has_metrics))
graph.add_edge(pydot.Edge(user_has_metrics, metrics_entity, label="1:n"))

graph.add_edge(pydot.Edge(metrics_entity, metrics_has_diagnosis))
graph.add_edge(pydot.Edge(metrics_has_diagnosis, diagnosis_entity, label="1:1"))

graph.add_edge(pydot.Edge(user_entity, user_has_sessions))
graph.add_edge(pydot.Edge(user_has_sessions, diagnosis_entity, label="1:n"))

# 连接User实体和其属性
graph.add_edge(pydot.Edge(user_entity, user_id))
graph.add_edge(pydot.Edge(user_entity, username))
graph.add_edge(pydot.Edge(user_entity, email))
graph.add_edge(pydot.Edge(user_entity, hashed_password))

# 连接VoiceMetrics实体和其属性
graph.add_edge(pydot.Edge(metrics_entity, metrics_id))
graph.add_edge(pydot.Edge(metrics_entity, voice_file_path))
graph.add_edge(pydot.Edge(metrics_entity, mfcc))
graph.add_edge(pydot.Edge(metrics_entity, delta))
graph.add_edge(pydot.Edge(metrics_entity, model_prediction))
graph.add_edge(pydot.Edge(metrics_entity, model_confidence))

# 连接DiagnosisSession实体和其属性
graph.add_edge(pydot.Edge(diagnosis_entity, session_id))
graph.add_edge(pydot.Edge(diagnosis_entity, session_time))
graph.add_edge(pydot.Edge(diagnosis_entity, llm_suggestion))
graph.add_edge(pydot.Edge(diagnosis_entity, llm_processed_at))

# 保存图表
graph.write_png(output_path)
print(f"✅  三角形布局ER图生成完毕: {output_path}")
