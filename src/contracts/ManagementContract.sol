pragma solidity^0.4.19;

import "./ManagementContractInterface.sol";
import "./lib/Ownable.sol";
import "./BatteryManagement.sol";
import "./ServiceProviderWallet.sol";
import "./ERC20.sol";

contract ManagementContract is Ownable {
  event Vendor(address, bytes4);
  event NewBattery(bytes4, bytes20);
  
  uint256 fee;
  ServiceProviderWallet public serviceProviderWallet;
  BatteryManagement public batteryManagement;

  mapping (address => bytes4) vendors;

  function ManagementContract(address _serviceProviderWallet, uint256 _fee) {
    serviceProviderWallet = ServiceProviderWallet(_serviceProviderWallet);
    fee = _fee;
  }

  function setBatteryManagementContract(address _batteryManagement) public onlyOwner {
    batteryManagement = BatteryManagement(_batteryManagement);
  }

  function setFee(uint256 _fee) public onlyOwner {
    fee = _fee;
  }

  function registerVendor(bytes _bytes) public payable {
    require(msg.value >= fee);
    bytes4 _bytes4 = bytes4(sha3(msg.sender, _bytes, block.number));
    vendors[msg.sender] = _bytes4;
    Vendor(msg.sender, _bytes4);
  }

  function registerBatteries(bytes20[] ids) public payable {
    require(vendors[msg.sender] != "");
    for (uint256 i = 0; i < ids.length; i++) {
      batteryManagement.createBattery(msg.sender, ids[i]);
      NewBattery(vendors[msg.sender], ids[i]);
    }
  }

  function() payable {}
}
