from pytoniq import Cell, Address, begin_cell, StateInit
from typing import TypedDict
import asyncio
import toml
import base64
from urllib.parse import urlencode


class Config(TypedDict):
    vanity_code: str
    salt: str
    code: str
    data: str
    owner_address: str
    target_address: str
    testnet: bool


async def main() -> None:
    config: Config = toml.load("config.toml")

    vanity_code: str = config["vanity_code"]
    salt: str = config["salt"]
    code: str = config["code"]
    data: str = config["data"]
    owner_address: str = config["owner_address"]
    target_address: Address = Address(config["target_address"])
    testnet: bool = config["testnet"]

    vanity_code: Cell = Cell.one_from_boc(vanity_code)

    code: Cell = Cell.one_from_boc(code)
    data: Cell = Cell.one_from_boc(data)

    vanity_data: Cell = (
        begin_cell()
        .store_uint(0, 5)
        .store_address(owner_address)
        .store_bytes(bytes.fromhex(salt))
        .end_cell()
    )

    deploy_init: StateInit = StateInit(
        code=vanity_code,
        data=vanity_data,
    )

    deploy_init_boc: str = base64.urlsafe_b64encode(
        deploy_init.serialize().to_boc(False)
    ).decode("utf-8").rstrip("=")

    deploy_body: Cell = begin_cell().store_ref(code).store_ref(data).end_cell()

    deploy_body_boc: str = base64.urlsafe_b64encode(deploy_body.to_boc(False)).decode(
        "utf-8"
    ).rstrip("=")

    target_hash_part: bytes = target_address.hash_part
    actual_hash_part: bytes = deploy_init.serialize().hash
    assert target_hash_part == actual_hash_part, (
        "state init hash != target address hash part"
    )

    uri_params: dict[str, str] = {
        "amount": int(1 * 1e9),
        "bin": deploy_body_boc,
        "init": deploy_init_boc,
        "testnet": str(testnet).lower(),
    }
    transfer_link: str = f"ton://transfer/{target_address.to_str()}?{urlencode(uri_params)}"

    print(transfer_link)


if __name__ == "__main__":
    asyncio.run(main())
