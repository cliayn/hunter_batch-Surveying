import argparse
import base64
import pandas as pd
import requests
import time
import itertools
from datetime import datetime

def construct_search_query(file_path):
    """构造搜索查询语句并编码"""
    try:
        df = pd.read_excel(file_path, header=0)
        search_queries = []

        # 分类处理各列
        all_columns = {}      # all-前缀列
        or_columns = {}       # |前缀列
        normal_columns = {}   # 普通列
        
        for column in df.columns:
            if pd.isna(column):
                continue
                
            col_name = str(column).strip()
            values = df[column].dropna().tolist()
            
            if col_name.startswith('all-'):
                # 处理all-列
                field = col_name[4:]
                all_columns[field] = values
            elif col_name.startswith('|'):
                # 处理OR列(需要至少2个值)
                field = col_name[1:]
                if len(values) >= 2:
                    or_columns[field] = values
                else:
                    print(f"忽略OR列'{col_name}'，因为值少于2个")
            else:
                # 普通列
                normal_columns[col_name] = values
        
        # 生成查询语句
        if all_columns:
            # 生成all列的全组合
            all_fields = list(all_columns.keys())
            value_combinations = itertools.product(*all_columns.values())
            
            for combo in value_combinations:
                query_terms = []
                
                # 1. 添加all-列组合条件
                for field, value in zip(all_fields, combo):
                    query_terms.append(f'{field}="{value}"')
                
                # 2. 添加普通列条件
                for col, vals in normal_columns.items():
                    for v in vals:
                        query_terms.append(f'{col}="{v}"')
                
                # 3. 添加OR列条件
                for col, vals in or_columns.items():
                    or_terms = [f'{col}="{v}"' for v in vals]
                    query_terms.append(f'({"||".join(or_terms)})')
                
                if query_terms:
                    search_queries.append(" && ".join(query_terms))
        else:
            # 处理没有all-列的情况
            query_terms = []
            # 添加普通列
            for col, vals in normal_columns.items():
                for v in vals:
                    query_terms.append(f'{col}="{v}"')
            # 添加OR列
            for col, vals in or_columns.items():
                or_terms = [f'{col}="{v}"' for v in vals]
                query_terms.append(f'({"||".join(or_terms)})')
            
            if query_terms:
                search_queries.append(" && ".join(query_terms))
        
        # 编码所有查询
        encoded_queries = []
        for query in search_queries:
            encoded = base64.urlsafe_b64encode(query.encode()).decode()
            encoded_queries.append((query, encoded))
        
        return encoded_queries if encoded_queries else None
            
    except Exception as e:
        print(f"解析Excel出错: {e}")
        return None

def query_api(api_key, encoded_query):
    """发送API请求"""
    url = "https://hunter.qianxin.com/openApi/search"
    params = {
        "api-key": api_key,
        "search": encoded_query,
        "page": 1,
        "page_size": 100
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if not data.get("data") or not isinstance(data["data"].get("arr"), list):
                print("API返回数据结构无效")
                return None
            return data
        print(f"API请求失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"请求发送失败: {e}")
    return None

def process_results(data, query_info=""):
    """处理API返回结果"""
    try:
        if not data or not data.get("data") or not isinstance(data["data"].get("arr"), list):
            print(f"{query_info} - 无有效数据")
            return None
            
        records = []
        for idx, item in enumerate(data["data"]["arr"], 1):
            try:
                components = ""
                if isinstance(item.get("component"), list):
                    components = ", ".join([
                        f"{c.get('name', '')}({c.get('version', '')})" 
                        for c in item["component"] 
                        if isinstance(c, dict)
                    ])
                
                location = "".join(filter(None, [
                    item.get('country', ''),
                    item.get('province', ''),
                    item.get('city', '')
                ]))
                
                records.append({
                    "序号": idx,
                    "ip": item.get("ip", ""),
                    "域名": item.get("domain", ""),
                    "端口": item.get("port", ""),
                    "站点标题": item.get("web_title", ""),
                    "状态码": item.get("status_code", ""),
                    "ICP备案企业": item.get("company", ""),
                    "应用/组件": components,
                    "资产标签": item.get("is_risk", ""),
                    "地理位置": location,
                    "更新时间": item.get("updated_at", ""),
                    "搜索条件": query_info
                })
            except Exception as e:
                print(f"处理记录时出错: {e}")
                continue
        
        return pd.DataFrame(records) if records else None
    except Exception as e:
        print(f"处理结果时出错: {e}")
        return None

def save_to_excel(df, filename):
    """保存为Excel文件"""
    try:
        if df is not None and not df.empty:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"result_{timestamp}.xlsx"
            df.to_excel(output_file, index=False, engine='openpyxl')
            print(f"结果已保存到: {output_file}")
            return output_file
        print("无有效数据可保存")
        return None
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='生成并发送搜索请求')
    parser.add_argument('-l', '--list', required=True, help='Excel文件路径')
    args = parser.parse_args()
    
    encoded_queries = construct_search_query(args.list)
    if not encoded_queries:
        print("无法生成有效的查询条件")
        return
    
    all_results = []
    api_key = "api"  # 替换为你的实际API-KEY
    
    for i, (query, encoded) in enumerate(encoded_queries, 1):
        print(f"\n正在执行查询({i}/{len(encoded_queries)}): {query}")
        result = query_api(api_key, encoded)
        
        if result:
            df = process_results(result, query)
            if df is not None:
                all_results.append(df)
        
        if i < len(encoded_queries):
            wait_time = 1  # 1秒间隔
            print(f"等待{wait_time}秒后继续...")
            time.sleep(wait_time)
    
    if all_results:
        try:
            final_df = pd.concat(all_results, ignore_index=True)
            save_to_excel(final_df, "result.xlsx")
        except Exception as e:
            print(f"合并结果时出错: {e}")
    else:
        print("未获取到任何有效结果")

if __name__ == "__main__":
    main()