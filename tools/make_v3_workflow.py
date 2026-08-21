# -*- coding: utf-8 -*-
"""把 minimax_h3_director 加速版工作流转换成 v3（sageattn3）版。
改动：MiniMaxH3MemoryEfficientSageAttentionPatch 节点 → PathchSageAttentionKJ(sageattn3)
用法：python make_v3_workflow.py <源工作流> <目标工作流>
"""
import json
import sys
import os

def make_v3(src, dst):
    d = json.load(open(src, encoding='utf-8'))
    changed = 0
    for n in d.get('nodes', []):
        if n.get('type') == 'MiniMaxH3MemoryEfficientSageAttentionPatch':
            n['type'] = 'PathchSageAttentionKJ'
            n['widgets_values'] = ["sageattn3"]
            n['properties'] = {"Node name for S&R": "PathchSageAttentionKJ"}
            # 输出名对齐（type 保持 MODEL 即可）
            for o in n.get('outputs', []):
                o['name'] = 'MODEL'
            changed += 1
    if not changed:
        print(f"❌ 未找到 MiniMaxH3MemoryEfficientSageAttentionPatch 节点: {src}")
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✅ v3 工作流已生成: {dst} (替换 {changed} 个节点)")
    return True

if __name__ == '__main__':
    make_v3(sys.argv[1], sys.argv[2])
