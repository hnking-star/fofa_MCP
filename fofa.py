import asyncio
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import base64

# 初始化一个mcp服务
mcp = FastMCP("fofasearch")

# Constants
OPENWEATHER_API_BASE = "https://fofa.info/api/v1/search/all"
USER_AGENT = "fofa-app/1.0"
#api密钥
OPENWEATHER_API_KEY = "your_fofa_key"


#核心工具函数：负责向openweater api发送请求，并且处理响应
async def make_nws_request(url: str) -> dict[str, Any] | None:
    """向openweather,api发送请求，并处理响应，包括适当的错误处理
    
    Args:
        url:请求的url
        
    Returns:
        dict[str,Any]:响应的json数据，如果请求失败则返回None
    """
    #设置请求头
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            #发送get请求，并且设置请求头和超时时间
            response = await client.get(url, headers=headers, timeout=30.0)
            #如果请求失败，则抛出异常
            response.raise_for_status()
            #返回json数据
            return response.json()
        except Exception as e:
            print(f"错误{e}")
            return None


#格式化警报特征，将其转换为可读文本格式
def format_alerts(alerts: list[list[str]]) -> str:
    """格式化FOFA搜索结果，将其转换为可读文本格式

    Args:
        alerts: FOFA API返回的结果数组，每个子数组包含[hostname, ip, port]

    Returns:
        str: 格式化后的文本，包含每个结果的主机名、IP和端口信息
    """
    if not alerts:
        return ""
    
    # 构建格式化的输出文本
    formatted_text = []
    for result in alerts:
        hostname, ip, port = result
        formatted_text.append(f"主机名: {hostname}\nIP地址: {ip}\n端口: {port}\n")
    
    # 用双换行符连接所有结果
    return "\n".join(formatted_text)


#告诉大模型以什么文本模式输出
@mcp.prompt()
async def search_prompt(query_params: str, assets_data: str) -> str:
    """生成包含资产上下文的安全分析提示词

    Args:
        query_params: 原始查询参数
        assets_data: 格式化后的资产数据

    Returns:
        str: 包含上下文的安全分析提示词
    """
    return (
        f"你是一个资深网络安全分析师，请基于以下查询条件：{query_params}\n"
        f"和发现的资产信息：\n{assets_data}\n\n"
        "请分析潜在安全风险并提供以下内容：\n"
        "1. 资产暴露面分析\n2. 潜在漏洞评估\n3. 加固建议"
    )


#注册接受
@mcp.tool()
async def get_alerts(
    domain: str = "",
    ip: str = "",
    port: str = "",
    host: str = "",
    body: str = "",
    icon_hash: str = "",
    icp: str = "",
    status_code: str = "200"
) -> dict[str, Any]:
    """FOFA网络引擎搜索资产，用户可以输入子域名，ip，端口号，主机名，网页内容，图标哈希，ICP备案号，HTTP状态码等参数，来找到
    网络的一些资产信息，然后继续渗透测试
    
    Args:
        domain: 域名
        ip: IP地址
        port: 端口
        host: 主机名
        body: 网页内容
        icon_hash: 图标哈希
        icp: ICP备案号
        status_code: HTTP状态码
        
    Returns:
        dict[str, Any]: FOFA搜索结果，包含error、results等字段
    """
    # 构建查询参数
    params = {}
    query_parts = []
    if domain:
        query_parts.append(f'domain="{domain}"')
    if ip:
        query_parts.append(f'ip="{ip}"')
    if port:
        query_parts.append(f'port="{port}"')
    if host:
        query_parts.append(f'host="{host}"')
    if body:
        query_parts.append(f'body="{body}"')
    if icon_hash:
        query_parts.append(f'icon_hash="{icon_hash}"')
    if icp:
        query_parts.append(f'icp="{icp}"')
    if status_code:
        query_parts.append(f'status_code={status_code}')
    
    # 使用&&连接所有查询条件并进行base64编码
    if query_parts:
        query_str = '&&'.join(query_parts)
        params['qbase64'] = base64.b64encode(query_str.encode()).decode()
    
    # 添加API密钥
    params['key'] = OPENWEATHER_API_KEY
    
    # 添加分页参数
    params['size'] = 1000
    
    # 构建完整URL
    url = f"{OPENWEATHER_API_BASE}?{httpx.QueryParams(params)}"
    print(url)
    # 发送请求并返回结果
    result = await make_nws_request(url)
   # print(result)
    if result is None:
        return {"error": "请求失败或无响应"}

    if result and 'results' in result:
        formatted_data = format_alerts(result['results'])
        # 构造原始查询参数
       # query_params = ', '.join([f'{k}={v}' for k, v in locals().items() if v and k not in ['self', 'kwargs']])
        # 生成最终提示词
       # final_prompt = await search_prompt(query_params, formatted_data)
       # return {"prompt": final_prompt, "data": formatted_data}
        return formatted_data
    else:
        print("未获取到有效结果")
        return {"error": "未找到匹配的资产"}






if __name__ == "__main__":
    print("MCP 11111服务正在启动...")
        # 测试URL构建
    result=asyncio.run(get_alerts())
    print(result)
   # if result and 'results' in result:
   #     formatted_data = format_alerts(result['results'])
     #   print("搜索结果:")
     #   print(formatted_data)
 #   else:
     #   print("未获取到有效结果")
    
    # 启动 MCP 服务
    print("启动 MCP 服务...")
    mcp.run(transport='stdio')
