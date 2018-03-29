pragma solidity^0.4.19;

import "./ERC20.sol";

contract Deal {

  enum State { invalid, waiting, agreementReceived, paid }

  State public state = State.invalid;

  bytes20 public oldBattery;
  bytes20 public newBattery;
  ERC20 erc20;
  uint256 public deprecationValue;
  uint256 public serviceFee;
  uint256 timeStub; // check assignment

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
  }

}
