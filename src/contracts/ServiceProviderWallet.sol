pragma solidity ^0.4.19;

import './lib/Ownable.sol';

contract ServiceProviderWallet is Ownable {
    // Для оповещения поступлении новых средств
    // - адрес, с которого перечислены средства
    // - сумма поступления
    event Received(address, uint256);

    // Для оповещения о выдачи части средств
    // - адрес, какой инициировал выдачу средств
    // - адрес, на который направлены средства
    // - сумма к выдаче
    event Withdraw(address, address, uint256);

    function () public payable {
        require(msg.value > 0);
        Received(msg.sender, msg.value);
    }

    // Используется для выдачи части средств с адреса контаркта
    function withdraw(address _to, uint256 _value) onlyOwner external {
        _to.transfer(_value);
        Withdraw(msg.sender, _to, _value);
    }

    // Позволяет удалить контракт
    function kill() onlyOwner external {
        selfdestruct(owner);
    }
}
