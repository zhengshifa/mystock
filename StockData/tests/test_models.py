"""
数据模型测试
"""
import pytest
from datetime import datetime
from src.models.stock_data import TickData, BarData, QuoteData


class TestQuoteData:
    """QuoteData模型测试"""
    
    def test_quote_data_creation(self):
        """测试QuoteData创建"""
        quote = QuoteData(
            bid_p=100.0,
            bid_v=1000,
            ask_p=101.0,
            ask_v=1000
        )
        
        assert quote.bid_p == 100.0
        assert quote.bid_v == 1000
        assert quote.ask_p == 101.0
        assert quote.ask_v == 1000


class TestTickData:
    """TickData模型测试"""
    
    def test_tick_data_creation(self):
        """测试TickData创建"""
        current_time = datetime.now()
        tick_data = TickData(
            symbol="600000",
            open=100.0,
            high=105.0,
            low=98.0,
            price=102.5,
            cum_volume=1000000,
            cum_amount=102500000.0,
            cum_position=0,
            trade_type=0,
            last_volume=1000,
            last_amount=102500.0,
            created_at=current_time,
            quotes=[
                QuoteData(bid_p=102.4, bid_v=1000, ask_p=102.6, ask_v=1000)
            ]
        )
        
        assert tick_data.symbol == "600000"
        assert tick_data.price == 102.5
        assert tick_data.created_at == current_time
        assert len(tick_data.quotes) == 1
        assert tick_data.data_hash != ""  # 应该自动生成哈希值
    
    def test_tick_data_hash_generation(self):
        """测试TickData哈希值生成"""
        current_time = datetime.now()
        tick_data1 = TickData(
            symbol="600000",
            price=100.0,
            created_at=current_time,
            cum_volume=1000
        )
        
        tick_data2 = TickData(
            symbol="600000",
            price=100.0,
            created_at=current_time,
            cum_volume=1000
        )
        
        # 相同数据应该生成相同的哈希值
        assert tick_data1.data_hash == tick_data2.data_hash


class TestBarData:
    """BarData模型测试"""
    
    def test_bar_data_creation(self):
        """测试BarData创建"""
        start_time = datetime.now().replace(hour=9, minute=30)
        end_time = datetime.now().replace(hour=15, minute=0)
        
        bar_data = BarData(
            symbol="600000",
            frequency="1d",
            open=100.0,
            close=102.0,
            high=105.0,
            low=98.0,
            amount=1000000.0,
            volume=10000,
            bob=start_time,
            eob=end_time
        )
        
        assert bar_data.symbol == "600000"
        assert bar_data.frequency == "1d"
        assert bar_data.open == 100.0
        assert bar_data.close == 102.0
        assert bar_data.bob == start_time
        assert bar_data.eob == end_time
        assert bar_data.data_hash != ""  # 应该自动生成哈希值
    
    def test_bar_data_hash_generation(self):
        """测试BarData哈希值生成"""
        start_time = datetime.now().replace(hour=9, minute=30)
        end_time = datetime.now().replace(hour=15, minute=0)
        
        bar_data1 = BarData(
            symbol="600000",
            frequency="1d",
            bob=start_time,
            eob=end_time
        )
        
        bar_data2 = BarData(
            symbol="600000",
            frequency="1d",
            bob=start_time,
            eob=end_time
        )
        
        # 相同数据应该生成相同的哈希值
        assert bar_data1.data_hash == bar_data2.data_hash


if __name__ == "__main__":
    pytest.main([__file__])
