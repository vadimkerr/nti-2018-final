pragma solidity^0.4.19;

import "./ManagementContractInterface.sol";
import "./lib/Ownable.sol";
import "./BatteryManagement.sol";
import "./ServiceProviderWallet.sol";
import "./ERC20.sol";

contract ManagementContract is ManagementContractInterface, Ownable {
  uint256 fee;
  ServiceProviderWallet serviceProviderWalletContract;
  BatteryManagement batteryManagementContract;

  function ManagementContract(address _currencyToken, uint256 _fee) {
    serviceProviderWallet = ServiceProviderWallet(serviceProviderWallet);
    fee = _fee;
  }

  function setBatteryManagementContract(address _batteryManagement) public onlyOwner {
    batteryManagement = BatteryManagement(_batteryManagement);
  }

  function setFee(uint256 _fee) public onlyOwner {
    fee = _fee;
  }
}
