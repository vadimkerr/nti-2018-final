pragma solidity ^0.4.19;

contract ERC20TokenInterface {
	// Общее количество выпущенных токенов
	function totalSupply() public view returns(uint256);

	// Для оповещения о перечислении части токенов новому владельцу
	// - предыдущий владелец
	// - текущий владелец
	// - количество токенов
	event Transfer(address indexed, address indexed, uint256);

	// Для оповещения, что какому-то аккунту делегировано право перечислять часть
	// токенов, которыми владеет другой аккаунт
	// - владелец токенов
	// - адрес далегата
	// - количество токенов, которыми может распоряжаться делегат
	event Approval(address indexed, address indexed, uint256);

	// Возвращает количество токенов, которыми владеет конкретный аккаунт
	// - адрес владельца токенов
	function balanceOf(address) public view returns(uint256);

	// Перечисляет токены от аккаунта-отправителя транзакции другому аккаунту.
	// Может выполняться, если аккаунт-отправитель тразанкции действительно
	// владеет достаточным количеством токенов. Генерирует событие Transfer.
	// - адрес получателя токенов
	// - количество токенов для отправки
	function transfer(address, uint256) public;

	// Делегирует право аккунту перечислять часть токенов, которыми владеет
	// аккаунт-отправитель транзакции. Может выполняться, если аккаунт-отправитель
	// тразанкции действительно владеет данным числом токенов. Если делегат уже
	// владел данным правом для какого-то числа токенов, то это ему
	// назначается право на новое количество токенов, старое право анулируется.
	// Генерирует событие Approval.
	// - адрес делегата
	// - количество токенов, которыми может распоряжаться делегат
	function approve(address, uint256) public;

	// Перечисляет указанное количество токенов от владельца к другому акаунту.
	// Может выполняться, только если отправителю транзакций делегировано право
	// перевода. Делегат не может перечислять больше того количества токенов,
	// на которое ему было дано право. Если аккаунт-владелец не обладает
	// достаточным количеством токенов, то токены не перводятся.
	// Генерирует событие Transfer.
	// - адрес владельца токенов
	// - адрес получателя токенов
	// - количество токенов
	function transferFrom(address, address, uint256) public;

	// Возрващает количество токенов, на перечисление которых делегировано
	// право.
	// - адрес владельца токенов
	// - адрес делегата
	function allowance(address, address) public view returns (uint256);

	// Производит эмиссию токенов и перечисляет их на указанный адрес.
	// Может выполняться только аккаунтами, обладающими соответствующим правом.
	// - адрес получателя новых токенов
	// - количество токенов, которое нужно эммитировать
	function mint(address, uint256) public;
}
