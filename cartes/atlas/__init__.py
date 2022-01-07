from .topo import GithubAPI, NpmAPI, TopoCatalogue

__all__ = ["default", "world_atlas"]

default = TopoCatalogue(
    api=GithubAPI(username="deldersveld", repository="topojson")
)

world_atlas = TopoCatalogue(api=NpmAPI(name="world-atlas@2.0.2"))


def __getattr__(name: str):
    return getattr(default, name)
