pragma solidity ^0.4.19;

import "./ManagementContractInterface.sol";
import "./lib/Ownable.sol";
import "./lib/SafeMath.sol";
import "./BatteryManagement.sol";
import "./ServiceProviderWallet.sol";
import "./ERC20.sol";

contract ManagementContract is Ownable {
  using SafeMath for uint256;

  event Vendor(address, bytes4);
  event NewBattery(bytes4, bytes20);

  struct vendor {
    bytes4 id;
    uint256 deposit;
  }

  uint256 public batteryFee;
  ServiceProviderWallet public serviceProviderWallet;
  BatteryManagement public batteryManagement;

  mapping (address => vendor) vendors;

  function ManagementContract(address _serviceProviderWallet, uint256 _batteryFee) {
    serviceProviderWallet = ServiceProviderWallet(_serviceProviderWallet);
    batteryFee = _batteryFee;
  }

  function setBatteryManagementContract(address _batteryManagement) public onlyOwner {
    batteryManagement = BatteryManagement(_batteryManagement);
  }

  function setFee(uint256 _batteryFee) public onlyOwner {
    batteryFee = _batteryFee;
  }

  function registerVendor(bytes _bytes) public payable {
    require(msg.value >= batteryFee.mul(1000));
    bytes4 _bytes4 = bytes4(keccak256(msg.sender, _bytes, block.number));
    vendors[msg.sender] = vendor(_bytes4, msg.value);
    Vendor(msg.sender, _bytes4);
  }

  function registerBatteries(bytes20[] ids) public payable {
    require(vendors[msg.sender].id != "");
    uint256 amount = ids.length;
    require(vendors[msg.sender].deposit >= batteryFee.mul(amount));
    for (uint256 i = 0; i < amount; i++) {
      batteryManagement.createBattery(msg.sender, ids[i]);
      NewBattery(vendors[msg.sender].id, ids[i]);
    }
  }

  function() payable {}
}
