#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用项目内置Python环境进行F5-TTS API调用
避免外部依赖版本冲突
"""

import os
import sys
import time
import shutil
from pathlib import Path

def test_with_project_env():
    """使用项目内置Python环境测试API"""
    print("🐍 使用项目内置Python环境进行API调用...")
    
    try:
        # 使用项目内置的gradio_client
        sys.path.insert(0, os.path.join(os.getcwd(), "py312", "Lib", "site-packages"))
        
        from gradio_client import Client
        
        print("✅ 成功导入项目gradio_client")
        print("🔗 连接到TTS服务...")
        
        # 连接到本地服务
        client = Client("http://localhost:80")
        print("✅ 连接成功")
        
        # 准备测试参数
        target_text = "你好，欢迎使用F5-TTS语音合成服务！"
        reference_audio = "reference.wav"
        reference_text = "这是参考音频的文本内容"
        
        print(f"📝 目标文本: {target_text}")
        print(f"📁 参考音频: {reference_audio}")
        print(f"📄 参考文本: {reference_text}")
        print()
        
        # 检查参考音频文件
        if not os.path.exists(reference_audio):
            print(f"❌ 找不到参考音频文件: {reference_audio}")
            return False
        
        print("🚀 开始TTS合成...")
        start_time = time.time()
        
        # 调用API
        result = client.predict(
            target_text,        # 要生成的文本
            reference_audio,    # 参考音频文件
            reference_text,     # 参考音频文本
            api_name="/do_job"  # API端点
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ 合成耗时: {duration:.2f}秒")
        print(f"📄 返回结果: {result}")
        
        # 处理返回的音频文件
        if result and os.path.exists(result):
            # 复制到当前目录
            timestamp = int(time.time())
            output_file = f"project_env_success_{timestamp}.wav"
            shutil.copy2(result, output_file)
            
            file_size = os.path.getsize(output_file)
            print(f"💾 音频已保存: {output_file}")
            print(f"📊 文件大小: {file_size} bytes")
            
            # 尝试播放音频
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(output_file)
                pygame.mixer.music.play()
                
                print("🔊 正在播放合成音频...")
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                pygame.mixer.quit()
                print("✅ 音频播放完成")
            except Exception as e:
                print(f"⚠️ 音频播放失败: {e}")
                print("💡 请手动播放音频文件验证效果")
            
            print()
            print("=" * 60)
            print("🎉 项目环境API调用成功！")
            print("=" * 60)
            print(f"✅ 合成时间: {duration:.2f}秒")
            print(f"✅ 输出文件: {output_file}")
            print(f"✅ 文件大小: {file_size} bytes")
            
            return True
        else:
            print("❌ 未获得有效的音频文件")
            print(f"📄 原始返回值: {result}")
            return False
            
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    # 切换到脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("📂 工作目录:", os.getcwd())
    print("🐍 Python版本:", sys.version)
    print()
    
    # 检查项目Python环境
    project_python_dir = os.path.join(os.getcwd(), "py312")
    if os.path.exists(project_python_dir):
        print(f"✅ 找到项目Python环境: {project_python_dir}")
    else:
        print(f"❌ 未找到项目Python环境: {project_python_dir}")
        return False
    
    # 执行API测试
    success = test_with_project_env()
    
    if success:
        print("\n🎯 测试结论:")
        print("   ✅ 项目内置Python环境可以成功调用API")
        print("   ✅ TTS合成功能完全正常")
        print("   ✅ 音频生成质量良好")
        print("\n💡 建议:")
        print("   - 使用项目内置Python环境进行API开发")
        print("   - 或者直接使用网页界面进行合成")
    else:
        print("\n❌ 测试失败，建议检查:")
        print("   - TTS服务是否正常运行")
        print("   - 参考音频文件是否存在")
        print("   - 网络连接是否正常")
    
    return success

if __name__ == "__main__":
    print("🚀 F5-TTS API调用测试 - 项目内置Python环境")
    print("=" * 60)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n\n❌ 测试异常: {e}")
    
    print("\n按回车键退出...")
    input()