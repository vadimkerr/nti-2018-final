pragma solidity ^0.4.19;

import "./BatteryManagementInterface.sol";
import "./ManagementContract.sol";
import "./ERC20.sol";
import "./Deal.sol";

contract BatteryManagement {
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

  struct battery {
    address vendor;
    address owner;
    uint256 charges;
  }

  ManagementContract public managementContract;
  ERC20 public erc20;

  mapping (bytes20 => battery) batteriesById;
  mapping (bytes32 => bool) history;

  function BatteryManagement(address _managementContract, address _token) {
    managementContract = ManagementContract(_managementContract);
    erc20 = ERC20(_token);
  }

  function createBattery(address _vendor, bytes20 _id) public onlyManager {
    batteriesById[_id].vendor = _vendor;
  }

  function transfer(address _newOwner, bytes20 _id) public batteryOwner(_id) {
    batteriesById[_id].owner = _newOwner;
    Transfer(batteriesById[_id].vendor, batteriesById[_id].owner, _id);
  }

  function ownerOf(bytes20 _id) public view returns (address) {
    require(batteriesById[_id].owner != address(0));
    return batteriesById[_id].owner;
  }

  function vendorOf(bytes20 _id) public view returns (address) {
    return batteriesById[_id].vendor;
  }

  function verifyBattery(uint256 n, uint256 t, uint8 v, bytes32 r, bytes32 s) public view returns (uint256, address) {
    uint256 m = n * 2**32 + t;
    bytes memory prefix = "\19Ethereum Signed Message:\n32";
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

  function initiateDeal(
      uint256 p,
      bytes32 rO,
      bytes32 sO,
      bytes32 rN,
      bytes32 sN,
      address car,
      uint256 amount
      ) public {
    // TODO: check if batteries are registered
    // TODO: check if owner of new_battery is legit scenter
    // TODO: check if owner of old_battery is legit car
    // TODO: check if msg.sender is legit scenter
    // TODO: check if scenter is the oner of any amount of batteries
    // TODO: check if the car is the real owner of the battery
    uint256 mO = p >> 160 * 2**32 + uint256(uint32(p >> 128));
    uint256 mN = uint256(uint16(p >> 64)) * 2**32 + uint256(uint8(p >> 32));
    bytes32 _prefixedHashO = keccak256("\19Ethereum Signed Message:\n32", keccak256(mO));
    bytes32 _prefixedHashN = keccak256("\19Ethereum Signed Message:\n32", keccak256(mN));
    // TODO: change 0-es to actual variables
    Deal deal = new Deal(bytes20(ecrecover(_prefixedHashO, uint8(uint24(p >> 96)), rO, sO)), bytes20(ecrecover(_prefixedHashN, uint8(p), rN, sN)), address(erc20), 0, amount, 0);
    NewDeal(address(deal));
  }

  function isBattery(address _id) internal view returns (bool) {
    return batteriesById[bytes20(_id)].vendor != address(0);
  }

  function inHistory(bytes32 _hash) internal view returns (bool) {
    return history[_hash];
  }

  function chargesNumber(bytes20 _id) public view returns (uint256) {
    return batteriesById[_id].charges;
  }
}
