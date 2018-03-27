pragma solidity ^0.4.19;

import "./ERC20TokenInterface.sol";
import "./lib/SafeMath.sol";
import "./lib/Ownable.sol";

contract ERC20 is Ownable {
  using SafeMath for uint256;

  event Transfer(address indexed, address indexed, uint256);
	event Approval(address indexed, address indexed, uint256);

  mapping (address => mapping (address => uint256)) internal allowed;

  mapping(address => uint256) balances;

  uint256 totalSupply_;

  function totalSupply() public view returns (uint256) {
    return totalSupply_;
  }

  function balanceOf(address _owner) public view returns (uint256 balance) {
    return balances[_owner];
  }

  function transfer(address _to, uint256 _value) public {
    require(_to != address(0));
    require(_value <= balances[msg.sender]);

    balances[msg.sender] = balances[msg.sender].sub(_value);
    balances[_to] = balances[_to].add(_value);
    Transfer(msg.sender, _to, _value);
  }

  function approve(address _spender, uint256 _value) public {
    allowed[msg.sender][_spender] = _value;
    Approval(msg.sender, _spender, _value);
  }

  function transferFrom(address _from, address _to, uint256 _value) public {
    require(_to != address(0));
    require(_value <= balances[_from]);
    require(_value <= allowed[_from][msg.sender]);

    balances[_from] = balances[_from].sub(_value);
    balances[_to] = balances[_to].add(_value);
    allowed[_from][msg.sender] = allowed[_from][msg.sender].sub(_value);
    Transfer(_from, _to, _value);
  }

  function allowance(address _owner, address _spender) public view returns (uint256) {
    return allowed[_owner][_spender];
  }

  function mint(address _to, uint256 _amount) public onlyOwner {
    totalSupply_ = totalSupply_.add(_amount);
    balances[_to] = balances[_to].add(_amount);
    Transfer(address(0), _to, _amount);
  }
}
