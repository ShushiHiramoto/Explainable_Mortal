import json
import gzip

input_file = 'built/dataset/test.mjson'
output_file = 'built/dataset/test.mjson.gz'

print("--- データの修正と圧縮を開始します ---")
fixed_count = 0

with open(input_file, 'r', encoding='utf-8') as f_in, gzip.open(output_file, 'wt', encoding='utf-8') as f_out:
    for line in f_in:
        if not line.strip():
            continue
        data = json.loads(line)
        
        # 局の開始イベントのとき、足りないフィールドを補完する
        if data.get('type') == 'start_kyoku':
            if 'kyotaku' not in data:
                data['kyotaku'] = 0
                
            if 'scores' not in data:
                data['scores'] = [25000, 25000, 25000, 25000]
            fixed_count += 1
            
        f_out.write(json.dumps(data) + '\n')

print(f"修復完了: {fixed_count} 局分のデータを最新形式に修正しました。")
print(f"保存先: {output_file}")