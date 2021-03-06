pragma solidity ^0.4.19;

import "./ERC20.sol";
import "./BatteryManagement.sol";
import "./ManagementContract.sol";

contract Deal {

  modifier isValid() {
    require(state != State.invalid);
    _;
  }

  modifier isWaiting() {
    require(state == State.waiting);
    _;
  }

  enum State { invalid, waiting, agreementReceived, paid }

  State public state = State.invalid;

  bytes20 public oldBattery;
  bytes20 public newBattery;
  ERC20 erc20;
  uint256 public deprecationValue;
  uint256 public serviceFee;
  uint256 timeStub; // check assignment

  BatteryManagement BC;
  ManagementContract MC;

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
    uint256 charges = BC.chargesNumber(oldBattery);
    address vendorAddress = BC.vendorOf(oldBattery);
    MC = ManagementContract(BC.managementContract());
    bytes4 vendorId = MC.vendorId(vendorAddress);
    bytes memory vendorName;

    uint256 k = 0;
    uint256 index = 0; */
/*
    while (MC.readName(vendorId, index) != "") {
      mem.push(MC.readName(vendorId, index));
      index += 32;
    }

    for (uint256 i = 0; i < mem.length; i++) {
      for (uint256 j = 0; j < mem[i].length; i++) {
        vendorName[k++] = mem[i][j];
      }
    }

    return (charges, vendorId, vendorName);
  } */

  /* function newBatteryInfo() public view returns (uint256, bytes4, bytes) {
    uint256 charges = BC.chargesNumber(newBattery);
    bytes4 vendorId = recoverName(BC.vendorOf(newBattery));
    MC = ManagementContract(BC.managementContract());
    bytes vendorName = recoverName(MC.readName(vendorId));
    return (charges, vendorId, vendorName);
  } */

  bytes32[] mem;

  /* function recoverName(bytes4 vendorId) public view returns (bytes name) {
    uint256 k = 0;
    uint256 index = 0;

    while (MC.readName(vendorId, index) != "") {
      mem.push(MC.readName(vendorId, index));
      index += 32;
    }

    for (uint256 i = 0; i < mem.length; i++) {
      for (uint256 j = 0; j < mem[i].length; i++) {
        name[k++] = mem[i][j];
      }
    }
  } */

  function agreeToDeal(uint256 p, bytes32 r, bytes32 s) public isWaiting {
    uint256 n = p >> 64;
    uint256 t = uint256(uint8(p >> 32));
    uint8 v = uint8(p);
    // implement me
    state = State.agreementReceived;
  }

  function confirmDeal(uint256 p, bytes32 r, bytes32 s) public isValid {
    uint256 n = p >> 64;
    uint256 t = uint256(uint8(p >> 32));
    uint8 v = uint8(p);
    // implement me
  }

  function verifyBattery(uint256 n, uint256 t, uint8 v, bytes32 r, bytes32 s) public view returns(uint256, address) {
    return BC.verifyBattery(n, t, v, r, s);
  }

  function cancelDeal() public isWaiting {
    if (!MC.serviceCenters(msg.sender)) {
      revert();
    }
    // implement me
    state = State.invalid;
  }
}
