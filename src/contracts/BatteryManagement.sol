pragma solidity^0.4.19;

import "./BatteryManagementInterface.sol";
import "./ManagementContract.sol";
import "./ERC20.sol";

contract BatteryManagement is BatteryManagementInterface {
  ManagementContract managementContract;
  ERC20 currencyToken;

  function BatteryManagement(address _managementContract, address _token) {
    managementContract = ManagementContracgt(_managementContract);
    currencyTokenContract = ERC20(_token);
  }

}
