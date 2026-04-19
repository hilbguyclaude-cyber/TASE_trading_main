"""
IBKR API Client using ib_insync.

Connects to IB Gateway for real order execution on TASE (Tel Aviv Stock Exchange).
Supports both paper trading (port 4002) and live trading (port 4001).
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
import os

try:
    from ib_insync import IB, Stock, MarketOrder, LimitOrder, Contract, Trade
    IB_INSYNC_AVAILABLE = True
except ImportError:
    IB_INSYNC_AVAILABLE = False
    if TYPE_CHECKING:
        from ib_insync import Contract


class IBKRConnectionError(Exception):
    """Raised when unable to connect to IB Gateway"""
    pass


class IBKROrderError(Exception):
    """Raised when order placement fails"""
    pass


class IBKRClient:
    """
    Interactive Brokers API client for TASE trading.

    Connects to IB Gateway running on EC2 and executes real orders.
    Uses ib_insync library for a synchronous API.
    """

    PAPER_PORT = 4002
    LIVE_PORT = 4001

    def __init__(
        self,
        host: str = '127.0.0.1',
        port: Optional[int] = None,
        client_id: int = 1,
        trading_mode: str = 'PAPER'
    ):
        """
        Initialize IBKR client.

        Args:
            host: IB Gateway host address
            port: IB Gateway port (auto-selected based on trading_mode if not specified)
            client_id: Unique client ID for this connection
            trading_mode: 'PAPER' or 'LIVE'
        """
        if not IB_INSYNC_AVAILABLE:
            raise ImportError("ib_insync is required. Install with: pip install ib_insync")

        self.host = host
        self.trading_mode = trading_mode.upper()

        if port is None:
            self.port = self.LIVE_PORT if self.trading_mode == 'LIVE' else self.PAPER_PORT
        else:
            self.port = port

        self.client_id = client_id
        self.ib = IB()
        self._connected = False

    def connect(self, timeout: int = 10) -> bool:
        """
        Connect to IB Gateway.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connection successful

        Raises:
            IBKRConnectionError: If connection fails
        """
        try:
            self.ib.connect(
                self.host,
                self.port,
                clientId=self.client_id,
                timeout=timeout,
                readonly=False
            )
            self._connected = self.ib.isConnected()

            if not self._connected:
                raise IBKRConnectionError(f"Failed to connect to IB Gateway at {self.host}:{self.port}")

            return True

        except Exception as e:
            self._connected = False
            raise IBKRConnectionError(f"Connection error: {e}")

    def disconnect(self) -> None:
        """Disconnect from IB Gateway"""
        if self._connected:
            self.ib.disconnect()
            self._connected = False

    def is_connected(self) -> bool:
        """Check if connected to IB Gateway"""
        return self._connected and self.ib.isConnected()

    def get_account(self) -> Optional[str]:
        """Get the connected account ID"""
        if not self.is_connected():
            return None
        accounts = self.ib.managedAccounts()
        return accounts[0] if accounts else None

    def _create_tase_contract(self, symbol: str) -> "Contract":
        """
        Create a TASE stock contract.

        Args:
            symbol: Stock symbol (e.g., 'TEVA', 'NICE')

        Returns:
            Qualified Contract object
        """
        contract = Stock(symbol, 'TASE', 'ILS')
        qualified = self.ib.qualifyContracts(contract)

        if not qualified:
            raise IBKROrderError(f"Unable to qualify contract for symbol: {symbol}")

        return qualified[0]

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Current price or None if unavailable
        """
        if not self.is_connected():
            raise IBKRConnectionError("Not connected to IB Gateway")

        try:
            contract = self._create_tase_contract(symbol)
            ticker = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(2)  # Wait for data

            price = ticker.marketPrice()
            self.ib.cancelMktData(contract)

            return price if price > 0 else None

        except Exception as e:
            raise IBKROrderError(f"Failed to get price for {symbol}: {e}")

    def place_order(
        self,
        symbol: str,
        quantity: int,
        action: str = 'BUY',
        order_type: str = 'MKT',
        limit_price: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Place an order on TASE.

        Args:
            symbol: Stock symbol (e.g., 'TEVA')
            quantity: Number of shares (positive integer)
            action: 'BUY' or 'SELL'
            order_type: 'MKT' (market) or 'LMT' (limit)
            limit_price: Required for limit orders

        Returns:
            Dict with order details including order_id, status, filled_qty, avg_price

        Raises:
            IBKRConnectionError: If not connected
            IBKROrderError: If order placement fails
        """
        if not self.is_connected():
            raise IBKRConnectionError("Not connected to IB Gateway")

        if action not in ('BUY', 'SELL'):
            raise IBKROrderError(f"Invalid action: {action}. Must be 'BUY' or 'SELL'")

        if quantity <= 0:
            raise IBKROrderError(f"Invalid quantity: {quantity}. Must be positive")

        try:
            contract = self._create_tase_contract(symbol)

            if order_type == 'MKT':
                order = MarketOrder(action, quantity)
            elif order_type == 'LMT':
                if limit_price is None:
                    raise IBKROrderError("Limit price required for limit orders")
                order = LimitOrder(action, quantity, limit_price)
            else:
                raise IBKROrderError(f"Invalid order type: {order_type}")

            trade: Trade = self.ib.placeOrder(contract, order)

            # Wait for order acknowledgment
            self.ib.sleep(1)

            return {
                'order_id': trade.order.orderId,
                'perm_id': trade.order.permId,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'order_type': order_type,
                'status': trade.orderStatus.status,
                'filled_qty': trade.orderStatus.filled,
                'avg_price': trade.orderStatus.avgFillPrice,
                'submitted_at': datetime.utcnow().isoformat()
            }

        except IBKROrderError:
            raise
        except Exception as e:
            raise IBKROrderError(f"Order placement failed: {e}")

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current position for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Dict with position details or None if no position
        """
        if not self.is_connected():
            raise IBKRConnectionError("Not connected to IB Gateway")

        try:
            positions = self.ib.positions()

            for pos in positions:
                if pos.contract.symbol == symbol and pos.contract.exchange == 'TASE':
                    return {
                        'symbol': symbol,
                        'quantity': pos.position,
                        'avg_cost': pos.avgCost,
                        'market_value': pos.position * pos.avgCost
                    }

            return None

        except Exception as e:
            raise IBKROrderError(f"Failed to get position for {symbol}: {e}")

    def get_all_positions(self) -> list[Dict[str, Any]]:
        """
        Get all current positions.

        Returns:
            List of position dictionaries
        """
        if not self.is_connected():
            raise IBKRConnectionError("Not connected to IB Gateway")

        try:
            positions = self.ib.positions()

            return [
                {
                    'symbol': pos.contract.symbol,
                    'exchange': pos.contract.exchange,
                    'quantity': pos.position,
                    'avg_cost': pos.avgCost,
                    'market_value': pos.position * pos.avgCost
                }
                for pos in positions
            ]

        except Exception as e:
            raise IBKROrderError(f"Failed to get positions: {e}")

    def cancel_order(self, order_id: int) -> bool:
        """
        Cancel an open order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancellation request sent
        """
        if not self.is_connected():
            raise IBKRConnectionError("Not connected to IB Gateway")

        try:
            open_orders = self.ib.openOrders()

            for order in open_orders:
                if order.orderId == order_id:
                    self.ib.cancelOrder(order)
                    return True

            return False

        except Exception as e:
            raise IBKROrderError(f"Failed to cancel order {order_id}: {e}")


class IBKRApiStub:
    """
    Stub for DRY_RUN mode - simulates IBKR API without real orders.

    Used when trading_mode is DRY_RUN. Logs actions but doesn't execute.
    """

    def __init__(self, trading_mode: str = 'DRY_RUN'):
        self.trading_mode = trading_mode
        self._connected = True
        self._order_counter = 1000
        self._positions: Dict[str, Dict] = {}

    def connect(self, timeout: int = 10) -> bool:
        print(f"[DRY_RUN] Would connect to IB Gateway")
        return True

    def disconnect(self) -> None:
        print(f"[DRY_RUN] Would disconnect from IB Gateway")

    def is_connected(self) -> bool:
        return self._connected

    def get_account(self) -> str:
        return "DRY_RUN_ACCOUNT"

    def get_current_price(self, symbol: str) -> Optional[float]:
        print(f"[DRY_RUN] Would get price for {symbol}")
        return None  # Let caller use fallback price source

    def place_order(
        self,
        symbol: str,
        quantity: int,
        action: str = 'BUY',
        order_type: str = 'MKT',
        limit_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Simulate order placement"""
        self._order_counter += 1

        print(f"[DRY_RUN] Would {action} {quantity} shares of {symbol} ({order_type})")

        result = {
            'order_id': self._order_counter,
            'perm_id': self._order_counter,
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'order_type': order_type,
            'status': 'SIMULATED',
            'filled_qty': quantity,
            'avg_price': 0.0,
            'submitted_at': datetime.utcnow().isoformat(),
            'dry_run': True
        }

        # Track simulated positions
        if action == 'BUY':
            self._positions[symbol] = {
                'symbol': symbol,
                'quantity': quantity,
                'avg_cost': 0.0
            }
        elif action == 'SELL' and symbol in self._positions:
            del self._positions[symbol]

        return result

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self._positions.get(symbol)

    def get_all_positions(self) -> list[Dict[str, Any]]:
        return list(self._positions.values())

    def cancel_order(self, order_id: int) -> bool:
        print(f"[DRY_RUN] Would cancel order {order_id}")
        return True


def get_ibkr_client(trading_mode: str = None) -> IBKRClient | IBKRApiStub:
    """
    Factory function to get the appropriate IBKR client.

    Args:
        trading_mode: 'DRY_RUN', 'PAPER', or 'LIVE' (reads from env if not specified)

    Returns:
        IBKRClient for PAPER/LIVE, IBKRApiStub for DRY_RUN
    """
    if trading_mode is None:
        trading_mode = os.environ.get('TRADING_MODE', 'DRY_RUN')

    trading_mode = trading_mode.upper()

    if trading_mode == 'DRY_RUN':
        return IBKRApiStub(trading_mode)

    host = os.environ.get('IBKR_GATEWAY_HOST', '127.0.0.1')
    client_id = int(os.environ.get('IBKR_CLIENT_ID', '1'))

    return IBKRClient(
        host=host,
        trading_mode=trading_mode,
        client_id=client_id
    )
