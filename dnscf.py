import requests
import traceback
import os
import json
from datetime import datetime, timezone, timedelta

# API 密钥
CF_API_TOKEN    =   os.environ["CF_API_TOKEN"]
CF_ZONE_ID      =   os.environ["CF_ZONE_ID"]
CF_DNS_NAME     =   os.environ["CF_DNS_NAME"]

# pushplus_token
PUSHPLUS_TOKEN  =   os.environ["PUSHPLUS_TOKEN"]

# headers
headers = {
    'Authorization': f'Bearer {CF_API_TOKEN}',
    'Content-Type': 'application/json'
}

def get_cf_speed_test_ip(timeout=10, max_retries=5):
    for attempt in range(max_retries):
        try:
            # 发送 GET 请求，设置超时
            response = requests.get('https://ip.164746.xyz/ipTop.html', timeout=timeout)
            # 检查响应状态码
            if response.status_code == 200:
                return response.text
        except Exception as e:
            traceback.print_exc()
            print(f"get_cf_speed_test_ip Request failed (attempt {attempt + 1}/{max_retries}): {e}")
    # 如果所有尝试都失败，返回 None 或者抛出异常，根据需要进行处理
    return None

# 获取 DNS 记录
def get_dns_records(name):
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records?name={name}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        records = response.json()['result']
        return [record['id'] for record in records]
    else:
        print('Error fetching DNS records:', response.text)
        return []

# 更新 DNS 记录
def update_dns_record(record_id, name, cf_ip):
    beijing_tz = timezone(timedelta(hours=8))
    comment_time = datetime.now(beijing_tz).strftime("cf-speed-dns: %Y/%m/%d %H:%M:%S")
    beijing_time = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records/{record_id}'
    data = {
        'type': 'A',
        'name': name,
        'content': cf_ip,
        'ttl': 3600,
        'comment': comment_time
    }
    # 提交
    response = requests.put(url, headers=headers, json=data)
    # 日志
    if response.status_code == 200:
        print(f"cf_dns_change success: ---- Time: {beijing_time} ---- ip：{cf_ip}")
        return f"ip:{cf_ip}解析{name}成功"
    else:
        print(f"cf_dns_change ERROR: ---- Time: {beijing_time} ---- MESSAGE: {response}")
        return f"ip:{cf_ip}解析{name}失败"

# 通知推送
def push_plus(content):
    url = 'http://www.pushplus.plus/send'
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": "IP优选DNSCF推送",
        "content": content,
        "template": "markdown",
        "channel": "wechat"
    }
    body = json.dumps(data).encode(encoding='utf-8')
    headers = {'Content-Type': 'application/json'}
    requests.post(url, data=body, headers=headers)

# 主函数
def main():
    # 获取最新优选IP
    ip_addresses_str = get_cf_speed_test_ip()
    ip_addresses = ip_addresses_str.split(',')
    best_ip = ip_addresses[0]
    # 执行 DNS 更新
    dns_records = get_dns_records(CF_DNS_NAME)
    push_plus_content = []
    if dns_records:
        dns = update_dns_record(dns_records[0], CF_DNS_NAME, best_ip)
        push_plus_content.append(dns)

    # 暂停通知
    # push_plus('\n'.join(push_plus_content))

if __name__ == '__main__':
    main()
