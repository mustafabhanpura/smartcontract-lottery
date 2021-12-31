from brownie import Lottery,accounts,config, network,exceptions
from scripts.deploy_lottery import deploy_lottery
import pytest

from web3 import Web3
import time

from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS,get_account,get_contract,fund_with_link

def test_get_enterance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    entrance_fee = lottery.getEntranceFee()
    expected_entrance_fee = Web3.toWei(0.025,"ether")
    assert expected_entrance_fee == entrance_fee

def test_cant_enter_unless_started():
    #arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    #act
    lottery = deploy_lottery()
    #assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from":get_account(),"value":lottery.getEntranceFee()})

def test_can_start_and_enter_lottery():
    #arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({'from':account})

    #act
    lottery.enter({"from":account,"value":lottery.getEntranceFee()})

    assert lottery.players(0) == account

def test_can_end_lottery():
     #arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({'from':account})
    lottery.enter({"from":account,"value":lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({'from':account})
    assert lottery.lottery_state() == 2

def test_can_select_winner_correctly():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({'from':account})
    lottery.enter({"from":account,"value":lottery.getEntranceFee()})
    lottery.enter({"from":get_account(index=1),"value":lottery.getEntranceFee()})
    lottery.enter({"from":get_account(index=2),"value":lottery.getEntranceFee()})
    fund_with_link(lottery)
    transaction = lottery.endLottery({"from":account})
    requestId =transaction.events['RequestedRandomness']['requestId']
    STATIC_RNG = 777
    get_contract('vrf_coordinator').callBackWithRandomness(
        requestId,STATIC_RNG,lottery.address,{"from":account}
    )

    starting_balance = account.balance()
    winning_amount = lottery.balance()
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance+winning_amount