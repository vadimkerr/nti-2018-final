pragma solidity ^0.4.19;

import "./ServiceProviderWallet.sol";
import "./BatteryManagement.sol";
import "./lib/Ownable.sol";

contract ManagementContract is Ownable {

    //Депозит для каждого вендора
    mapping (address => uint256) public vendorDeposit;

    //По адресу отправителя определяет имя производителя которое ему принадлежит
    mapping (address => bytes4) public vendorId;

    //По индефикатору возвращает имя производителя
    mapping (bytes4 => bytes) public vendorNames;

    //Проверка уже зарегестрированного имени
    mapping (bytes => bool) registeredVendor;

    // Возвращает истину или ложь в зависимости от того, зарегистрирован
    // электромобиль с указанным адресом в системе или нет.
    mapping (address => bool) public serviceCenters;

    // Возвращает истину или ложь в зависимости от того, зарегистрирован
    // электромобиль с указанным адресом в системе или нет.
    mapping (address => bool) public cars;

    // Контракт управляющий информацией о батареях
    BatteryManagement public batteryManagement;
    // Контракт кошелька
    ServiceProviderWallet public walletContract;

    //Цена за создание одной батареи
    uint256 BatFee;
    
    // Для оповещения регистрации нового производителя
    // - адрес аккаунта из-под которого проходила регистрация
    // - идентификатор производителя
    event Vendor(address owner, bytes4 tokenId);

    // Для оповещения о создании новой батареи
    // - идентификатор производителя
    // - идентификатор батареи
    event NewBattery(bytes4 vendorId, bytes20 tokenId);

    // Конструктор контракта
    // - адрес контракта, ответственного за накопление криптовалюты,
    //   перечисляемой в качестве депозита за использование сервиса.
    // - сумму сбора за выпуск одной батареи
    function ManagementContract(address _wallet, uint256 _batfee) public{
        BatFee = _batfee;
        walletContract = ServiceProviderWallet(_wallet);
    }

    // Устанавливает адрес для контракта, ответственного за
    // управление информацией о батареях.
    // Доступен только создателю management контракта
    // - адрес контракта, управляющего инфорацией о батареях
    function setBatteryManagementContract(address _batmgmt) onlyOwner public {
        batteryManagement = BatteryManagement(_batmgmt);
    }

    // Регистрирует вендора, если при вызове метода перечисляется
    // достаточно средств.
    // - наименование производителя
    function registerVendor(bytes _name) public payable{
        require(msg.value >= BatFee*1000);
        require(!registeredVendor[_name]);
        require(vendorId[msg.sender] == "");

        registeredVendor[_name] = true;

        bytes4 _nameSym = bytes4(keccak256(msg.sender,_name,block.number));
        
        vendorDeposit[msg.sender] += msg.value;
        address(walletContract).transfer(msg.value);

        vendorId[msg.sender] = _nameSym;
        vendorNames[_nameSym] = _name;

        Vendor(msg.sender,_nameSym);
    }

    // Регистрирует новые батареи, если при вызове метода на балансе
    // данного производителя достаточно средств. Во время регистрации
    // батарей баланс уменьшается соответственно количеству батареи и
    // цене, установленной для данного производителя на текущий момент.
    // - идентификаторы батарей
    function registerBatteries(bytes20[] _ids) public payable{
        uint _n = _ids.length;
        require(msg.value + vendorDeposit[msg.sender] >= _n * BatFee);
        
        bytes4 _tokenId = vendorId[msg.sender];
        require(_tokenId != "");
        
        vendorDeposit[msg.sender] += msg.value - (_n * BatFee);
        if (msg.value > 0){
            address(walletContract).transfer(msg.value);
        }
        
        for (uint i=0; i < _n; i++){
            batteryManagement.createBattery(msg.sender, _ids[i]);
            NewBattery(_tokenId, _ids[i]);
        }

    }

    // Регистрирует в системе адрес отправителя транзакции, как сервис центр.
    // Регистрация просиходит только если данный адрес уже не был зарегистрирован
    // в качестве сервис центра или электромобиля.
    function registerServiceCenter() public{
        require(!cars[msg.sender]);
        require(!serviceCenters[msg.sender]);
        serviceCenters[msg.sender] = true;
    }

    // Регистрирует в системе адрес отправителя транзакции, электромобиль.
    // Регистрация просиходит только если данный адрес уже не был зарегистрирован
    // в качестве сервис центра или электромобиля.
    function registerCar() public{
        require(!cars[msg.sender]);
        require(!serviceCenters[msg.sender]);
        cars[msg.sender] = true;
    }
}
