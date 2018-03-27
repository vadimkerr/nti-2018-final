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

  ManagementContract public managementContract;
  ERC20 public erc20;

  mapping (address => bytes20[]) batteries;

  function BatteryManagement(address _managementContract, address _token) {
    managementContract = ManagementContract(_managementContract);
    erc20 = ERC20(_token);
  }

  function createBattery(address vendor, bytes20 id) public onlyManager {
    batteries[vendor].push(id);
  }
}
