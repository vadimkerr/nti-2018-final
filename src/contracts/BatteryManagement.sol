pragma solidity ^0.4.19;

import "./ManagementContract.sol";
import "./ERC20.sol";
import "./Deal.sol";
import "./lib/Ownable.sol";

contract BatteryManagement is Ownable{
  event Transfer(address indexed, address indexed, bytes20);
  event Approval(address indexed, address indexed, bytes20);
  event NewDeal(address);

  modifier onlyManager() {
    require(msg.sender == address(managementContract));
    _;
  }

  modifier batteryOwner(bytes20 _id) {
    if (batteriesById[_id].owner == address(0)) {
      require(msg.sender == batteriesById[_id].vendor);
      _;
    } else {
      require(msg.sender == batteriesById[_id].owner);
      _;
    }
  }

  modifier registered(address _who) {
    require(managementContract.serviceCenters(_who) || managementContract.cars(_who));
    _;
  }

  struct battery {
    address vendor;
    address owner;
    uint256 charges;
    bool inDeal;
  }

  ManagementContract public managementContract;
  ERC20 public erc20;

  uint256 public timeoutThreshold;

  mapping (bytes20 => battery) public batteriesById;
  mapping (bytes32 => bool) history; // sure?
  mapping (address => mapping (address => bytes20)) allowed;

  function BatteryManagement(address _managementContract, address _token) {
    managementContract = ManagementContract(_managementContract);
    erc20 = ERC20(_token);
  }

  function createBattery(address _vendor, bytes20 _id) public onlyManager {
    require(batteriesById[_id].vendor == address(0));
    batteriesById[_id].vendor = _vendor;
  }

  function transfer(address _newOwner, bytes20 _id) public batteryOwner(_id) registered(_newOwner) {
    batteriesById[_id].owner = _newOwner;
    Transfer(batteriesById[_id].vendor, batteriesById[_id].owner, _id);
  }

  function approve(address _deal, bytes20 _id) public {
    require(msg.sender == ownerOf(_id));

    allowed[msg.sender][_deal] = _id;

    Approval(msg.sender, _deal, _id);
  }

  function ownerOf(bytes20 _id) public view returns (address) {
    if (batteriesById[_id].owner == address(0)) {
      return batteriesById[_id].vendor;
    } else {
      return batteriesById[_id].owner;
    }
  }

  function vendorOf(bytes20 _id) public view returns (address) {
    return batteriesById[_id].vendor;
  }

  function chargesNumber(bytes20 _id) public view returns (uint256) {
    return batteriesById[_id].charges;
  }

  function setTimeoutThreshold(uint256 _time) public onlyOwner {
    timeoutThreshold = _time;
  }

  function verifyBattery(uint256 n, uint256 t, uint8 v, bytes32 r, bytes32 s) public view returns (uint256, address) {
    uint256 m = n * 2**32 + t;
    bytes memory prefix = "\x19Ethereum Signed Message:\n32";
    bytes32 _hash = keccak256(m);
    bytes32 prefixedHash = keccak256(prefix, _hash);
    address _id = ecrecover(prefixedHash, v, r, s);

    if (isBattery(_id)) {
      return (0, batteriesById[bytes20(_id)].vendor);
    } else if (inHistory(keccak256(m))) {
      return (1, address(0));
    } else if (!isBattery(_id)) {
      return (2, address(0));
    }
    return (999, address(0));
  }

  function recoverAddress(uint256 n, uint256 t, uint8 v, bytes32 r, bytes32 s) internal view returns (address) {
    uint256 m = n * 2**32 + t;
    bytes memory prefix = "\x19Ethereum Signed Message:\n32";
    bytes32 _hash = keccak256(m);
    bytes32 prefixedHash = keccak256(prefix, _hash);
    return ecrecover(prefixedHash, v, r, s);
  }

  function initiateDeal(
      uint256 p,
      bytes32 rO,
      bytes32 sO,
      bytes32 rN,
      bytes32 sN,
      address car,
      uint256 amount
      ) public {
    require(managementContract.serviceCenters(msg.sender));
    require(managementContract.cars(car));

    address _addressO;
    address _addressN;

    (, _addressO) = verifyBattery(p >> 160, uint256(uint32(p >> 128)), uint8(uint24(p >> 96)), rO, sO);
    (, _addressN) = verifyBattery(uint256(uint16(p >> 64)), uint256(uint8(p >> 32)), uint8(p), rN, sN);

    require(address(_addressO) != address(0) && address(_addressN) != address(0));

    _addressO = recoverAddress(p >> 160, uint256(uint32(p >> 128)), uint8(uint24(p >> 96)), rO, sO);
    _addressN = recoverAddress(uint256(uint16(p >> 64)), uint256(uint8(p >> 32)), uint8(p), rN, sN);

    require(batteriesById[bytes20(_addressO)].owner == car);
    require(batteriesById[bytes20(_addressN)].owner == msg.sender);
    require(!batteriesById[bytes20(_addressO)].inDeal && !batteriesById[bytes20(_addressN)].inDeal);

    batteriesById[bytes20(_addressO)].charges = p >> 160;
    batteriesById[bytes20(_addressN)].charges = uint256(uint16(p >> 64));

    history[bytes20(_addressO)] = true;
    history[bytes20(_addressN)] = true;

    // TODO: last param is timeStub
    Deal deal = new Deal(bytes20(_addressO), bytes20(_addressN), address(erc20), compensation(p >> 160, uint256(uint16(p >> 64))), amount, 3600);

    approve(address(deal), bytes20(_addressN));

    NewDeal(address(deal));
  }

  function compensation(uint256 nO, uint256 nN) internal view returns (uint256) {
    require(nO >= 0 && nN >= 0);

    uint256 caseO = _case(nO);
    uint256 caseN = _case(nN);

    uint256 delta;

    if (nO >= nN) {
      delta = nO - nN;
    }

    if (caseO == caseN) {
      return delta * 1 ether;
    } else if ((caseO == 1 && caseN == 0) || (caseO == 2 && caseN == 1)) {
      return delta * 1003**delta * 1 finney;
    } else if (caseO == 3 && caseN != 3) {
      return 1000 ether;
    } else if (caseO == 2 && caseN == 0) {
      return delta * 1003500**delta * 1 szabo;
    } else {
      return 0;
    }
  }

  function _case(uint256 n) internal pure returns (uint256) {
    if (n < 50) {
      return 0;
    } else if (n >= 50 && n < 150) {
      return 1;
    } else if (n >= 150 && n < 300) {
      return 2;
    } else if (n > 300) {
      return 3;
    }
  }

  function isBattery(address _id) internal view returns (bool) {
    return batteriesById[bytes20(_id)].vendor != address(0);
  }

  function inHistory(bytes32 _hash) internal view returns (bool) {
    return history[_hash];
  }
}
