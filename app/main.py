from argparse import ArgumentParser
from database import main


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(main.app)

