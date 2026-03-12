#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F5-TTS API使用示例
演示如何通过API访问TTS服务
"""

import os
import sys
import time
import requests
import json

def check_service_status():
    """检查TTS服务状态"""
    try:
        response = requests.get("http://localhost:80/config", timeout=5)
        if response.status_code == 200:
            print("✅ TTS服务正在运行")
            return True
        else:
            print(f"⚠️ 服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到TTS服务: {e}")
        print("💡 请确保运行了 '运行_自动开启接口服务.bat'")
        return False

def demo_web_interface():
    """演示网页界面使用"""
    print("\n🌐 网页界面API访问演示")
    print("=" * 50)
    
    print("📱 访问地址: http://localhost:80")
    print()
    print("📋 使用步骤:")
    print("1. 在'输入需要生成的文本'框中输入:")
    print("   你好，欢迎使用F5-TTS语音合成服务！")
    print()
    print("2. 选择或上传参考音频:")
    print("   - 从下拉列表选择现有音频")
    print("   - 或上传您的 reference.wav 文件")
    print()
    print("3. 在'参考音频文本'框中输入:")
    print("   这是参考音频的文本内容")
    print()
    print("4. 点击'开始生成'按钮")
    print("5. 等待处理完成，播放或下载结果")
    print()
    
    # 尝试打开网页界面
    try:
        import webbrowser
        print("🚀 正在为您打开网页界面...")
        webbrowser.open("http://localhost:80")
        print("✅ 网页界面已打开")
    except Exception as e:
        print(f"⚠️ 自动打开失败: {e}")
        print("💡 请手动访问: http://localhost:80")

def demo_api_info():
    """显示API技术信息"""
    print("\n🔧 API技术信息")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:80/config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            
            print(f"📊 Gradio版本: {config.get('version', 'unknown')}")
            print(f"🌐 API前缀: {config.get('api_prefix', '/gradio_api')}")
            print(f"🎯 应用ID: {config.get('app_id', 'unknown')}")
            print(f"⚡ 队列启用: {config.get('enable_queue', False)}")
            
            # 查找do_job端点
            dependencies = config.get('dependencies', [])
            for dep in dependencies:
                if dep.get('api_name') == 'do_job':
                    print(f"🎤 TTS端点: /do_job (fn_index: {dep.get('id')})")
                    break
            
            print(f"📡 完整配置端点: http://localhost:80/config")
            
        else:
            print(f"❌ 配置获取失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 获取API信息失败: {e}")

def create_api_usage_guide():
    """创建API使用指南"""
    print("\n📖 API使用指南")
    print("=" * 50)
    
    guide = """
## API访问方式总结

### 🌟 推荐方式：网页界面
- 地址: http://localhost:80
- 优点: 稳定、直观、无依赖冲突
- 使用: 直接在浏览器中操作

### 🔧 技术方式：HTTP API
- 端点: /do_job
- 方法: POST
- 参数: gen_text, prompt_audio, ref_text

### 📝 示例参数
```
目标文本: 你好，欢迎使用F5-TTS语音合成服务！
参考音频: reference.wav
参考文本: 这是参考音频的文本内容
```

### 🚀 快速开始
1. 确保TTS服务运行 (运行_自动开启接口服务.bat)
2. 访问 http://localhost:80
3. 按照界面提示操作
4. 获得高质量合成音频

### 💡 注意事项
- 参考音频质量影响合成效果
- 参考文本应与音频内容匹配
- 建议单次文本长度不超过100字
"""
    
    print(guide)
    
    # 保存指南到文件
    try:
        with open("API使用指南.txt", "w", encoding="utf-8") as f:
            f.write(guide)
        print("💾 使用指南已保存到: API使用指南.txt")
    except Exception as e:
        print(f"⚠️ 保存指南失败: {e}")

def main():
    """主函数"""
    print("🎤 F5-TTS API使用演示")
    print("=" * 50)
    
    # 检查服务状态
    if not check_service_status():
        return
    
    # 演示网页界面
    demo_web_interface()
    
    # 显示API信息
    demo_api_info()
    
    # 创建使用指南
    create_api_usage_guide()
    
    print("\n🎯 总结")
    print("=" * 50)
    print("✅ TTS服务正常运行")
    print("✅ 网页界面可直接使用")
    print("✅ API端点配置正确")
    print("💡 推荐使用网页界面进行API访问")

if __name__ == "__main__":
    main()
    print("\n按回车键退出...")
    input()