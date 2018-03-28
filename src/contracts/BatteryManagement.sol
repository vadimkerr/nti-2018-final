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

  /* function verifyBattery(uint256 n, uint256 t, uint8 v, bytes32 r, bytes32 s) public view returns (uint256, address) {
    uint256 m = n * 2**32 + t;
    address _id = ecrecover(keccak256(m), v, r, s);
    if (isBattery(_id)) {
      return (0, batteriesById[_id].vendor);
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
    // TODO: create Deal contract with constructor arguments(?)
    Deal deal = new Deal();
    NewDeal(address(deal));
  } */

  function isBattery(address _id) internal view returns (bool) {
    return batteriesById[bytes20(_id)].vendor != address(0);
  }

  function inHistory(bytes32 _hash) internal view returns (bool) {
    return history[_hash];
  }
}
