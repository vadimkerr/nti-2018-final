pragma solidity^0.4.19;

import "./ERC20.sol";
import "./BatteryManagement.sol";

contract Deal {

  enum State { invalid, waiting, agreementReceived, paid }

  State public state = State.invalid;

  bytes20 public oldBattery;
  bytes20 public newBattery;
  ERC20 erc20;
  uint256 public deprecationValue;
  uint256 public serviceFee;
  uint256 timeStub; // check assignment

  BatteryManagement BC;

  function Deal(
    bytes20 _idO,
    bytes20 _idN,
    address _erc20,
    uint256 _deprecationValue,
    uint256 _serviceFee,
    uint256 _timeStub
    ) public {
    oldBattery = _idO;
    newBattery = _idN;
    erc20 = ERC20(_erc20);
    deprecationValue = _deprecationValue;
    serviceFee = _serviceFee;
    timeStub = _timeStub; // not default

    state = State.waiting;

    BC = BatteryManagement(msg.sender);
  }

  /* function oldBatteryInfo() public view returns (uint256, bytes4, bytes) {
    bytes4 _id = BC.batteriesById[oldBattery].id;
    bytes _name = BC.batteriesById[oldBattery].name;
    return (BC.batteriesById[oldBattery].charges, _id, _name);
  }

  function newBatteryInfo() public view returns (uint256, bytes4, bytes) {
    bytes4 _id = BC.batteriesById[newBattery].id;
    bytes _name = BC.batteriesById[newBattery].name;
    return (BC.batteriesById[newBattery].charges, _id, _name);
  } */
}
