"""Tests for IBKR client implementation."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from lib.ibkr_client import (
    IBKRClient,
    IBKRApiStub,
    IBKRConnectionError,
    IBKROrderError,
    get_ibkr_client,
    IB_INSYNC_AVAILABLE
)


class TestIBKRApiStub:
    """Tests for the DRY_RUN stub implementation."""

    def test_stub_initializes_connected(self):
        stub = IBKRApiStub()
        assert stub.is_connected() is True
        assert stub.trading_mode == 'DRY_RUN'

    def test_stub_connect_returns_true(self):
        stub = IBKRApiStub()
        assert stub.connect() is True

    def test_stub_get_account_returns_dry_run(self):
        stub = IBKRApiStub()
        assert stub.get_account() == "DRY_RUN_ACCOUNT"

    def test_stub_get_current_price_returns_none(self):
        stub = IBKRApiStub()
        assert stub.get_current_price('TEVA') is None

    def test_stub_place_buy_order(self):
        stub = IBKRApiStub()
        result = stub.place_order('TEVA', 100, 'BUY', 'MKT')

        assert result['symbol'] == 'TEVA'
        assert result['action'] == 'BUY'
        assert result['quantity'] == 100
        assert result['status'] == 'SIMULATED'
        assert result['dry_run'] is True
        assert 'order_id' in result

    def test_stub_place_sell_order(self):
        stub = IBKRApiStub()
        stub.place_order('TEVA', 100, 'BUY', 'MKT')
        result = stub.place_order('TEVA', 100, 'SELL', 'MKT')

        assert result['action'] == 'SELL'
        assert result['status'] == 'SIMULATED'

    def test_stub_tracks_positions(self):
        stub = IBKRApiStub()

        assert stub.get_position('TEVA') is None

        stub.place_order('TEVA', 100, 'BUY', 'MKT')
        pos = stub.get_position('TEVA')
        assert pos is not None
        assert pos['quantity'] == 100

        stub.place_order('TEVA', 100, 'SELL', 'MKT')
        assert stub.get_position('TEVA') is None

    def test_stub_get_all_positions(self):
        stub = IBKRApiStub()
        stub.place_order('TEVA', 100, 'BUY', 'MKT')
        stub.place_order('NICE', 50, 'BUY', 'MKT')

        positions = stub.get_all_positions()
        assert len(positions) == 2

    def test_stub_cancel_order_returns_true(self):
        stub = IBKRApiStub()
        assert stub.cancel_order(1001) is True

    def test_stub_disconnect(self):
        stub = IBKRApiStub()
        stub.disconnect()


class TestGetIBKRClient:
    """Tests for the factory function."""

    def test_dry_run_returns_stub(self):
        client = get_ibkr_client('DRY_RUN')
        assert isinstance(client, IBKRApiStub)

    def test_dry_run_case_insensitive(self):
        client = get_ibkr_client('dry_run')
        assert isinstance(client, IBKRApiStub)

    @patch.dict('os.environ', {'TRADING_MODE': 'DRY_RUN'})
    def test_reads_env_when_none(self):
        client = get_ibkr_client(None)
        assert isinstance(client, IBKRApiStub)

    @pytest.mark.skipif(not IB_INSYNC_AVAILABLE, reason="ib_insync not installed")
    def test_paper_returns_ibkr_client(self):
        client = get_ibkr_client('PAPER')
        assert isinstance(client, IBKRClient)
        assert client.port == 4002

    @pytest.mark.skipif(not IB_INSYNC_AVAILABLE, reason="ib_insync not installed")
    def test_live_returns_ibkr_client(self):
        client = get_ibkr_client('LIVE')
        assert isinstance(client, IBKRClient)
        assert client.port == 4001


@pytest.mark.skipif(not IB_INSYNC_AVAILABLE, reason="ib_insync not installed")
class TestIBKRClient:
    """Tests for the real IBKR client (mocked ib_insync)."""

    def test_client_initializes_with_defaults(self):
        client = IBKRClient()
        assert client.host == '127.0.0.1'
        assert client.port == 4002
        assert client.trading_mode == 'PAPER'
        assert client._connected is False

    def test_client_live_mode_uses_port_4001(self):
        client = IBKRClient(trading_mode='LIVE')
        assert client.port == 4001

    def test_client_custom_port_overrides_default(self):
        client = IBKRClient(port=9999, trading_mode='PAPER')
        assert client.port == 9999

    @patch('lib.ibkr_client.IB')
    def test_connect_success(self, mock_ib_class):
        mock_ib = Mock()
        mock_ib.isConnected.return_value = True
        mock_ib_class.return_value = mock_ib

        client = IBKRClient()
        client.ib = mock_ib
        result = client.connect()

        assert result is True
        assert client._connected is True
        mock_ib.connect.assert_called_once()

    @patch('lib.ibkr_client.IB')
    def test_connect_failure_raises_error(self, mock_ib_class):
        mock_ib = Mock()
        mock_ib.connect.side_effect = Exception("Connection refused")
        mock_ib_class.return_value = mock_ib

        client = IBKRClient()
        client.ib = mock_ib

        with pytest.raises(IBKRConnectionError) as exc_info:
            client.connect()

        assert "Connection error" in str(exc_info.value)
        assert client._connected is False

    @patch('lib.ibkr_client.IB')
    def test_disconnect(self, mock_ib_class):
        mock_ib = Mock()
        mock_ib.isConnected.return_value = True
        mock_ib_class.return_value = mock_ib

        client = IBKRClient()
        client.ib = mock_ib
        client._connected = True
        client.disconnect()

        assert client._connected is False
        mock_ib.disconnect.assert_called_once()

    @patch('lib.ibkr_client.IB')
    def test_is_connected_checks_both_flags(self, mock_ib_class):
        mock_ib = Mock()
        mock_ib_class.return_value = mock_ib

        client = IBKRClient()
        client.ib = mock_ib

        client._connected = True
        mock_ib.isConnected.return_value = True
        assert client.is_connected() is True

        client._connected = True
        mock_ib.isConnected.return_value = False
        assert client.is_connected() is False

        client._connected = False
        mock_ib.isConnected.return_value = True
        assert client.is_connected() is False

    @patch('lib.ibkr_client.IB')
    def test_get_account_returns_first_account(self, mock_ib_class):
        mock_ib = Mock()
        mock_ib.isConnected.return_value = True
        mock_ib.managedAccounts.return_value = ['DUQ238485', 'DUQ238486']
        mock_ib_class.return_value = mock_ib

        client = IBKRClient()
        client.ib = mock_ib
        client._connected = True

        assert client.get_account() == 'DUQ238485'

    @patch('lib.ibkr_client.IB')
    def test_place_order_validates_action(self, mock_ib_class):
        mock_ib = Mock()
        mock_ib.isConnected.return_value = True
        mock_ib_class.return_value = mock_ib

        client = IBKRClient()
        client.ib = mock_ib
        client._connected = True

        with pytest.raises(IBKROrderError) as exc_info:
            client.place_order('TEVA', 100, 'INVALID', 'MKT')

        assert "Invalid action" in str(exc_info.value)

    @patch('lib.ibkr_client.IB')
    def test_place_order_validates_quantity(self, mock_ib_class):
        mock_ib = Mock()
        mock_ib.isConnected.return_value = True
        mock_ib_class.return_value = mock_ib

        client = IBKRClient()
        client.ib = mock_ib
        client._connected = True

        with pytest.raises(IBKROrderError) as exc_info:
            client.place_order('TEVA', 0, 'BUY', 'MKT')

        assert "Invalid quantity" in str(exc_info.value)

    @patch('lib.ibkr_client.IB')
    def test_place_order_requires_limit_price_for_lmt(self, mock_ib_class):
        mock_ib = Mock()
        mock_ib.isConnected.return_value = True
        mock_ib.qualifyContracts.return_value = [Mock()]
        mock_ib_class.return_value = mock_ib

        client = IBKRClient()
        client.ib = mock_ib
        client._connected = True

        with pytest.raises(IBKROrderError) as exc_info:
            client.place_order('TEVA', 100, 'BUY', 'LMT', limit_price=None)

        assert "Limit price required" in str(exc_info.value)

    @patch('lib.ibkr_client.IB')
    def test_place_order_not_connected_raises_error(self, mock_ib_class):
        mock_ib = Mock()
        mock_ib.isConnected.return_value = False
        mock_ib_class.return_value = mock_ib

        client = IBKRClient()
        client.ib = mock_ib
        client._connected = False

        with pytest.raises(IBKRConnectionError) as exc_info:
            client.place_order('TEVA', 100, 'BUY', 'MKT')

        assert "Not connected" in str(exc_info.value)

    @patch('lib.ibkr_client.IB')
    @patch('lib.ibkr_client.Stock')
    @patch('lib.ibkr_client.MarketOrder')
    def test_place_market_order_success(self, mock_market_order, mock_stock, mock_ib_class):
        mock_ib = Mock()
        mock_ib.isConnected.return_value = True

        mock_contract = Mock()
        mock_ib.qualifyContracts.return_value = [mock_contract]

        mock_trade = Mock()
        mock_trade.order.orderId = 12345
        mock_trade.order.permId = 67890
        mock_trade.orderStatus.status = 'Submitted'
        mock_trade.orderStatus.filled = 0
        mock_trade.orderStatus.avgFillPrice = 0.0
        mock_ib.placeOrder.return_value = mock_trade

        mock_ib_class.return_value = mock_ib

        client = IBKRClient()
        client.ib = mock_ib
        client._connected = True

        result = client.place_order('TEVA', 100, 'BUY', 'MKT')

        assert result['order_id'] == 12345
        assert result['symbol'] == 'TEVA'
        assert result['action'] == 'BUY'
        assert result['quantity'] == 100
        assert result['status'] == 'Submitted'

    @patch('lib.ibkr_client.IB')
    def test_get_all_positions(self, mock_ib_class):
        mock_ib = Mock()
        mock_ib.isConnected.return_value = True

        mock_pos = Mock()
        mock_pos.contract.symbol = 'TEVA'
        mock_pos.contract.exchange = 'TASE'
        mock_pos.position = 100
        mock_pos.avgCost = 50.0
        mock_ib.positions.return_value = [mock_pos]

        mock_ib_class.return_value = mock_ib

        client = IBKRClient()
        client.ib = mock_ib
        client._connected = True

        positions = client.get_all_positions()

        assert len(positions) == 1
        assert positions[0]['symbol'] == 'TEVA'
        assert positions[0]['quantity'] == 100
        assert positions[0]['avg_cost'] == 50.0
