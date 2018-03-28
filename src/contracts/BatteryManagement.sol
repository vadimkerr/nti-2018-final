pragma solidity ^0.4.19;

import "./BatteryManagementInterface.sol";
import "./ManagementContract.sol";
import "./ERC20.sol";

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
}
