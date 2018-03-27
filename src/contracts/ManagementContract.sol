pragma solidity ^0.4.19;

import "./ManagementContractInterface.sol";
import "./lib/Ownable.sol";
import "./lib/SafeMath.sol";
import "./BatteryManagement.sol";
import "./ServiceProviderWallet.sol";
import "./ERC20.sol";

contract ManagementContract is Ownable {
  using SafeMath for uint256;

  modifier uniqueName(bytes _bytes) {
    require(!names[_bytes]);
    _;
  }

  event Vendor(address, bytes4);
  event NewBattery(bytes4, bytes20);

  struct vendor {
    bytes4 id;
    uint256 deposit;
    uint256 fee;
  }

  uint256 batfee;
  ServiceProviderWallet public serviceProviderWallet;
  BatteryManagement public batteryManagement;

  mapping (address => vendor) vendors;
  mapping (bytes => bool) names;
  mapping (address => bool) serviceCenters;
  mapping (address => bool) cars;

  function ManagementContract(address _serviceProviderWallet, uint256 _batteryFee) {
    serviceProviderWallet = ServiceProviderWallet(_serviceProviderWallet);
    batfee = _batteryFee;
  }

  function setBatteryManagementContract(address _batteryManagement) public onlyOwner {
    batteryManagement = BatteryManagement(_batteryManagement);
  }

  function setFee(uint256 _batteryFee) public onlyOwner {
    batfee = _batteryFee;
  }

  function batteryFee() public view returns (uint256) {
    if (vendors[msg.sender].fee > 0) {
      return vendors[msg.sender].fee;
    }
    return batfee;
  }

  function registerVendor(bytes _bytes) public payable uniqueName(_bytes) {
    require(msg.value >= registrationDeposit());
    require(vendors[msg.sender].id == "");
    bytes4 _bytes4 = bytes4(keccak256(msg.sender, _bytes, block.number));
    vendors[msg.sender] = vendor(_bytes4, msg.value, batfee);
    names[_bytes] = true;
    Vendor(msg.sender, _bytes4);
  }

  function vendorDeposit(address _vendor) public view returns (uint256) {
    return vendors[_vendor].deposit;
  }

  function registerBatteries(bytes20[] ids) public payable {
    require(vendors[msg.sender].id != "");
    vendors[msg.sender].deposit.add(msg.value);
    uint256 amount = ids.length;
    require(vendors[msg.sender].deposit >= amount.mul(vendors[msg.sender].fee));
    for (uint256 i = 0; i < amount; i++) {
      batteryManagement.createBattery(msg.sender, ids[i]);
      vendors[msg.sender].deposit.sub(vendors[msg.sender].fee);
      NewBattery(vendors[msg.sender].id, ids[i]);
    }
  }

  function registrationDeposit() public view returns (uint256) {
    return batfee.mul(1000);
  }

  function registerServiceCenter() public {
    require(!serviceCenters[msg.sender]);
    require(!cars[msg.sender]);
    serviceCenters[msg.sender] = true;
  }

  function registerCar() public {
    require(!serviceCenters[msg.sender]);
    require(!cars[msg.sender]);
    cars[msg.sender] = true;
  }

  function() payable {}
}
