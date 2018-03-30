pragma solidity ^0.4.19;

import "./lib/Ownable.sol";
import "./lib/SafeMath.sol";
import "./BatteryManagement.sol";
import "./ServiceProviderWallet.sol";

contract ManagementContract is Ownable {
  using SafeMath for uint256;

  modifier uniqueName(bytes _bytes) {
    require(!names[_bytes]);
    _;
  }

  event Vendor(address, bytes4);
  event NewBattery(bytes4, bytes20);
  event NewName(bytes);

  struct vendor {
    bytes4 id;
    uint256 deposit;
    uint256 fee;
  }

  uint256 batfee;
  ServiceProviderWallet public walletContract;
  BatteryManagement public batteryManagement;

  mapping (address => vendor) public vendors;
  mapping (bytes4 => bytes) public vendorNames;
  mapping (bytes => bool) names;
  mapping (address => bool) public serviceCenters;
  mapping (address => bool) public cars;

  // Custom method
  function pleaseGetName(bytes4 _id) public view returns (bytes) {
    return vendorNames[_id];
  }

  // Custom method
  function isNameUnique(bytes _name) public view returns (bool) {
    return names[_name];
  }

  // Custom method
  function isUnique() public view returns (bool) {
    return (vendors[msg.sender].id == "");
  }

  function vendorId(address _vendor) public view returns (bytes4) {
    return vendors[_vendor].id;
  }

  function ManagementContract(address _serviceProviderWallet, uint256 _batteryFee) {
    walletContract = ServiceProviderWallet(_serviceProviderWallet);
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
    vendorNames[_bytes4] = _bytes;
    names[_bytes] = true;
    NewName(_bytes);
    Vendor(msg.sender, _bytes4);
    require(walletContract.send(msg.value));
  }

  function vendorDeposit(address _vendor) public view returns (uint256) {
    return vendors[_vendor].deposit;
  }

  function registerBatteries(bytes20[] ids) public payable {
    require(vendors[msg.sender].id != "");
    if (msg.value > 0) {
      address(walletContract).transfer(msg.value);
      vendors[msg.sender].deposit = vendors[msg.sender].deposit.add(msg.value);
    }
    uint256 amount = ids.length;
    uint256 totalCost = amount.mul(vendors[msg.sender].fee);
    require(vendors[msg.sender].deposit >= totalCost);

    vendors[msg.sender].deposit = vendors[msg.sender].deposit.sub(totalCost);
    for (uint256 i = 0; i < amount; i++) {
      batteryManagement.createBattery(msg.sender, ids[i]);
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
