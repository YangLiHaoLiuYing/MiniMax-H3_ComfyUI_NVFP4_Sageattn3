# -*- coding: utf-8 -*-
"""把 Director 全部示例工作流转成 v3（sageattn3）版。
统一规则：
  1. 删除链路上的所有 attention patch 节点（H3 patch 或旧 KJ 节点）
  2. 新建 PathchSageAttentionKJ(sageattn3) 节点
  3. 重连: UNETLoader --MODEL--> KJ(sageattn3) --MODEL--> MiniMaxH3Director
用法: python make_v3_workflows.py <src_dir> <dst_dir>
"""
import json
import glob
import os
import sys

PATCH_TYPES = ('MiniMaxH3MemoryEfficientSageAttentionPatch', 'PathchSageAttentionKJ')

def make_v3_workflow(src, dst):
    d = json.load(open(src, encoding='utf-8'))
    nodes = d.get('nodes', [])
    links = d.get('links', [])

    unet = next((n for n in nodes if n.get('type') == 'UNETLoader'), None)
    director = next((n for n in nodes if n.get('type') == 'MiniMaxH3Director'), None)
    if unet is None or director is None:
        print(f'  ⏭️ 跳过(缺 UNETLoader/Director): {os.path.basename(src)}')
        return False

    # 1) 删除 patch 类节点，记录被删节点 id
    removed_ids = {n['id'] for n in nodes if n.get('type') in PATCH_TYPES}
    nodes = [n for n in nodes if n['id'] not in removed_ids]

    # 2) 删除涉及被删节点的 links
    links = [l for l in links if l[1] not in removed_ids and l[3] not in removed_ids]

    # 3) 新建 KJ 节点
    new_id = max(n['id'] for n in nodes) + 1
    kj_node = {
        "id": new_id,
        "type": "PathchSageAttentionKJ",
        "pos": [unet['pos'][0] + 300, unet['pos'][1]],
        "size": [315, 58],
        "flags": {},
        "order": max(n.get('order', 0) for n in nodes) + 1,
        "mode": 4,
        "inputs": [{"name": "model", "type": "MODEL", "link": None}],
        "outputs": [{"name": "MODEL", "type": "MODEL", "links": [], "slot_index": 0}],
        "properties": {"Node name for S&R": "PathchSageAttentionKJ"},
        "widgets_values": ["sageattn3"]
    }
    nodes.append(kj_node)

    # 4) 找最大 link id 并新建两条 link
    max_link = max(l[0] for l in links) if links else 0
    l1 = max_link + 1  # UNET.out0 -> KJ.in0
    l2 = max_link + 2  # KJ.out0 -> Director.in0

    # 更新 UNET 输出
    for o in unet.get('outputs', []):
        if o.get('type') == 'MODEL':
            o['links'] = [l1]
    # 更新 KJ 输入输出
    kj_node['inputs'][0]['link'] = l1
    kj_node['outputs'][0]['links'] = [l2]
    # 更新 Director 的 model 输入（inputs[0]）
    dir_model_in = director.get('inputs', [{}])[0]
    dir_model_in['link'] = l2

    # 5) 重建 links 数组
    links.append([l1, unet['id'], 0, new_id, 0, 'MODEL'])
    links.append([l2, new_id, 0, director['id'], 0, 'MODEL'])

    d['nodes'] = nodes
    d['links'] = links

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f'  ✅ {os.path.basename(dst)} (删 {len(removed_ids)} patch, 新增 KJ id={new_id})')
    return True

if __name__ == '__main__':
    src_dir, dst_dir = sys.argv[1], sys.argv[2]
    pats = sorted(glob.glob(os.path.join(src_dir, '*.json')))
    print(f'源目录: {src_dir} ({len(pats)} 个工作流)')
    for p in pats:
        fn = os.path.basename(p)
        base = fn[:-5]  # 去掉 .json
        dst = os.path.join(dst_dir, f'{base}_v3.json')
        make_v3_workflow(p, dst)
