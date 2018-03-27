pragma solidity^0.4.19;

import "./BatteryManagementInterface.sol";
import "./ManagementContract.sol";
import "./ERC20.sol";

contract BatteryManagement is BatteryManagementInterface {
  modifier onlyManager() {
    require(msg.sender == managementContract);
    _;
  }

  ManagementContract managementContract;
  ERC20 currencyToken;

  mapping (address => []bytes20) batteries;

  function BatteryManagement(address _managementContract, address _token) {
    managementContract = ManagementContracgt(_managementContract);
    currencyTokenContract = ERC20(_token);
  }

  function createBattery(address vendor, bytes20 id) public onlyManager {
    batteries[vendor].push(id);
  }
}
