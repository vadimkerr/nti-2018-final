pragma solidity ^0.4.19;

import "./NFT/BasicNFToken.sol";
import "./ManagementContract.sol";
import "./ERC20Token.sol";
import "./lib/Ownable.sol";

contract BatteryManagement is BasicNFToken, Ownable {
    // Для оповещения о передаче прав владения батареей новому владельцу
    // - адрес предыдущего владельца
    // - адрес нового владельца
    // - индентификатор батареи
    event Transfer(address indexed, address indexed, bytes20);
    
    ManagementContract public managementContract;
    ERC20Token public erc20;

    // Конструктор контракта
    // - адрес контракта, управляющего списком вендоров.
    // - адрес контракта, управляющего токенами, в которых будет
    //   происходить расчет за замену батарей.
    function BatteryManagement(address _mgmt, address _erc20) public {
        managementContract = ManagementContract(_mgmt);
        erc20 = ERC20Token(_erc20);
    }
    
    // Создает новую батарею
    // Владельцем батареи назначается его текущий создатель.
    // Создание нового батареи может быть доступно только 
    // management контракту
    // - адрес производителя батареи
    // - идентификатор батареи
    function createBattery(address _vendor, bytes20 _tokenId) public {
        require(msg.sender == address(managementContract));
        require(!batteryExists(_tokenId));
        _setTokenWithID(_tokenId, _vendor);
        _transfer(0, _vendor, _tokenId);
    }
    
    // Возвращает адрес производителя батареи
    // - идентификатор батареи
    function vendorOf(bytes20 _batteryId) view public returns(address) {
        return tokenID[_batteryId];
    }
    
    // Проверяет зарегистрирован ли токен с таким идентификатором любым из производителей.
    function batteryExists(bytes20 _batteryId) internal view returns (bool) {
        return tokenID[_batteryId] != address(0);
    }
}
