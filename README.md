## About

This repo is the image manipulation demo of "[Self-Supervised Scene De-occlusion](https://github.com/XiaohangZhan/deocclusion)".

* Below is the demo.

<img src="manipulation.gif" width=500>

For further information, please contact [Xiaohang Zhan](https://xiaohangzhan.github.io/).

## Usage

1. Clone the repo, install dependencies.

    ```shell
    git clone https://github.com/XiaohangZhan/deocclusion-demo
    pip install PyQt5, opencv-python
    ```

2. Run the demo.

    ```shell
    python main.py
    ```

3. Interactions.

    * Click `Open` to open an image from `decomposition/image_*.png`.
    * Click `De-occlusion` to load decomposed components.
    * Use mouse to drag objects.
    * Mouse right click to change ordering or save the object.
    * Click `Show Objects` to show each object in order.
    * Click `Reset` to reset to the original status.
    * Click `Insert` and open an image from `materials` to insert it.
    * Push `Up` or `Down` arrow button to zoom out or zoom in the object.
    * Push `Left` or `Right` arrow button to rotate the object.
    * Click `Save As` to save the re-composed image.

4. Try new images.

* First of all, you should launch the jupyter notebooks [here](https://github.com/XiaohangZhan/deocclusion/blob/master/demos/), e.g., `demo_cocoa.ipynb`.

* Second, run the notebook up to the last cell. In the last cell, change the `False` under `# save` to `True`. In this way, the completed objects as well as the background are saved following the topological order under `outputs/decomposition/`.

* Third, copy the image as well as the folder containing the decomposed components under `decomposition` in this repo. Then enjoy yourself to re-compose the image.

## Notice

There are still some bugs. Since I have no time to fix them, you are welcome to raise pull request to fix them. The bugs are below:

* When you click `Open` or `Insert` to browse a folder, but choose cancel, the program crash.
