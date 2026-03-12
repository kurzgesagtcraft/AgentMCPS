"""
x402 支付验证系统
支持 Base 链支付验证、交易追踪和收益记录

Author: Kilo Code
Version: 2.0.0
"""

import asyncio
import json
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import hmac

# 模拟区块链调用（实际应使用 web3.py 或 alchemy SDK）
# 在生产环境中，这些导入将是真实的：
# from web3 import Web3
# from alchemy import Alchemy, Network

class PaymentStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class PaymentRecord:
    """支付记录"""
    tx_hash: str
    from_address: str
    to_address: str
    amount: str
    currency: str
    chain_id: int
    status: PaymentStatus
    tool_name: str
    timestamp: str
    block_number: Optional[int] = None
    confirmation: int = 0


@dataclass
class PaymentConfig:
    """支付配置"""
    price_usdc: str
    pay_to_address: str
    chain_id: int = 8453  # Base Mainnet
    currency: str = "USDC"
    asset_address: str = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # Base USDC
    min_confirmations: int = 1


class X402PaymentVerifier:
    """
    x402 支付验证器
    
    功能：
    1. 验证支付证明
    2. 追踪链上交易
    3. 记录收益流水
    """
    
    def __init__(self, config: PaymentConfig):
        self.config = config
        self.payment_history: List[PaymentRecord] = []
        self._load_payment_history()
        
        # 初始化 Web3 连接（示例配置）
        # self.w3 = Web3(Web3.HTTPProvider(os.getenv('BASE_RPC_URL')))
        # self.alchemy = Alchemy(api_key=os.getenv('ALCHEMY_API_KEY'))
    
    def _get_history_file(self) -> str:
        """获取支付历史文件路径"""
        return 'kiloAgent/finance/x402_payments.json'
    
    def _load_payment_history(self):
        """加载支付历史"""
        history_file = self._get_history_file()
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.payment_history = [
                        PaymentRecord(**record) for record in data
                    ]
            except Exception as e:
                print(f"[x402] 加载支付历史失败: {e}")
    
    def _save_payment_history(self):
        """保存支付历史"""
        history_file = self._get_history_file()
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        
        with open(history_file, 'w') as f:
            json.dump(
                [
                    {
                        'tx_hash': r.tx_hash,
                        'from_address': r.from_address,
                        'to_address': r.to_address,
                        'amount': r.amount,
                        'currency': r.currency,
                        'chain_id': r.chain_id,
                        'status': r.status.value,
                        'tool_name': r.tool_name,
                        'timestamp': r.timestamp,
                        'block_number': r.block_number,
                        'confirmation': r.confirmation
                    }
                    for r in self.payment_history
                ],
                f,
                indent=2
            )
    
    def generate_payment_requirements(self, tool_name: str) -> Dict[str, Any]:
        """
        生成 x402 支付要求（用于返回 402 错误响应）
        
        Returns:
            符合 x402 规范的支付要求字典
        """
        return {
            "x402Version": "1",
            "requires": {
                "scheme": "exact",
                "network": f"eip155:{self.config.chain_id}",
                "maxAmountRequired": self.config.price_usdc,
                "asset": self.config.asset_address,
                "payTo": self.config.pay_to_address,
                "resource": f"mcp://tool/{tool_name}",
                "description": f"Kilo Code {tool_name} Service Fee"
            },
            "expires": datetime.now().isoformat() + "Z"
        }
    
    async def verify_payment_proof(self, payment_proof: Dict, tool_name: str) -> PaymentRecord:
        """
        验证支付证明
        
        Args:
            payment_proof: 客户端提交的支付证明
            tool_name: 被调用的工具名称
        
        Returns:
            验证后的支付记录
        """
        # 解析支付证明
        tx_hash = payment_proof.get('txHash') or payment_proof.get('transactionHash')
        from_address = payment_proof.get('from') or payment_proof.get('payer')
        amount = payment_proof.get('amount')
        
        if not tx_hash or not from_address:
            raise ValueError("支付证明缺少必要的字段: txHash, from")
        
        # 验证支付金额
        if float(amount) < float(self.config.price_usdc):
            raise ValueError(
                f"支付金额不足: 收到 {amount}, 需要 {self.config.price_usdc}"
            )
        
        # 验证交易（实际应调用链上验证）
        record = await self._verify_onchain(tx_hash, from_address, amount, tool_name)
        
        # 保存支付记录
        self.payment_history.append(record)
        self._save_payment_history()
        
        return record
    
    async def _verify_onchain(
        self, 
        tx_hash: str, 
        from_address: str, 
        amount: str, 
        tool_name: str
    ) -> PaymentRecord:
        """
        验证链上交易（实际实现应使用 web3.py 或 Alchemy SDK）
        
        模拟实现：
        - 检查交易是否已确认
        - 验证收款地址正确
        - 验证金额正确
        """
        # 模拟链上验证
        # 实际实现：
        # tx = self.w3.eth.get_transaction(tx_hash)
        # receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        # 
        # 验证逻辑：
        # 1. receipt.status == 1 (交易成功)
        # 2. tx.to == self.config.pay_to_address (收款地址正确)
        # 3. tx.value >= required_amount (金额足够)
        # 4. receipt.block_number + min_confirmations <= current_block
        
        record = PaymentRecord(
            tx_hash=tx_hash,
            from_address=from_address,
            to_address=self.config.pay_to_address,
            amount=amount,
            currency=self.config.currency,
            chain_id=self.config.chain_id,
            status=PaymentStatus.VERIFIED,
            tool_name=tool_name,
            timestamp=datetime.now().isoformat(),
            block_number=12345678,  # 模拟区块号
            confirmation=self.config.min_confirmations
        )
        
        print(f"[x402] 支付验证成功: {tx_hash[:16]}... | 金额: {amount} {self.config.currency}")
        return record
    
    async def get_payment_status(self, tx_hash: str) -> Optional[PaymentRecord]:
        """
        获取支付状态
        
        Args:
            tx_hash: 交易哈希
        
        Returns:
            支付记录或 None
        """
        return next(
            (r for r in self.payment_history if r.tx_hash == tx_hash),
            None
        )
    
    def get_revenue_summary(self) -> Dict[str, Any]:
        """
        获取收入摘要
        
        Returns:
            包含总收入、交易数等信息的字典
        """
        verified_payments = [
            r for r in self.payment_history 
            if r.status == PaymentStatus.VERIFIED
        ]
        
        total_revenue = sum(float(r.amount) for r in verified_payments)
        
        return {
            "total_transactions": len(self.payment_history),
            "verified_transactions": len(verified_payments),
            "total_revenue_usdc": total_revenue,
            "pending_payments": len([
                r for r in self.payment_history 
                if r.status == PaymentStatus.PENDING
            ]),
            "failed_payments": len([
                r for r in self.payment_history 
                if r.status == PaymentStatus.FAILED
            ])
        }


class X402PaymentMiddleware:
    """
    x402 支付中间件
    用于集成到 MCP 服务器中
    """
    
    def __init__(self, verifier: X402PaymentVerifier):
        self.verifier = verifier
    
    async def check_payment(self, payment_proof: Optional[Dict], tool_name: str) -> bool:
        """
        检查支付是否存在且有效
        
        Args:
            payment_proof: 支付证明（可选）
            tool_name: 工具名称
        
        Returns:
            是否允许访问
        """
        if not payment_proof:
            return False
        
        try:
            await self.verifier.verify_payment_proof(payment_proof, tool_name)
            return True
        except Exception as e:
            print(f"[x402] 支付验证失败: {e}")
            return False
    
    def get_payment_requirements(self, tool_name: str) -> Dict[str, Any]:
        """
        获取支付要求（用于返回 402 错误）
        """
        return self.verifier.generate_payment_requirements(tool_name)


def create_x402_verifier() -> X402PaymentVerifier:
    """
    创建 x402 验证器（从配置文件读取配置）
    """
    config = PaymentConfig(
        price_usdc="0.01",  # 默认价格 0.01 USDC
        pay_to_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # Kilo Code 收款地址
        chain_id=8453,  # Base Mainnet
        currency="USDC",
        asset_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # Base USDC
    )
    
    return X402PaymentVerifier(config)


# 示例用法
async def main():
    """示例主函数"""
    print("="*60)
    print(" x402 支付验证系统测试 ")
    print("="*60)
    
    # 创建验证器
    verifier = create_x402_verifier()
    middleware = X402PaymentMiddleware(verifier)
    
    # 生成支付要求
    requirements = middleware.get_payment_requirements("Click-Tool")
    print("\n[Payment Requirements]:")
    print(json.dumps(requirements, indent=2))
    
    # 模拟支付证明
    mock_payment = {
        "txHash": "0x" + "a" * 64,
        "from": "0x1234567890abcdef1234567890abcdef12345678",
        "amount": "0.02"
    }
    
    # 验证支付
    result = await middleware.check_payment(mock_payment, "Click-Tool")
    print(f"\n[Payment Verification]: {'SUCCESS' if result else 'FAILED'}")
    
    # 收入摘要
    summary = verifier.get_revenue_summary()
    print(f"\n[Revenue Summary]:")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())