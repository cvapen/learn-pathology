from django.db import models
import fast
import time
import numpy as np
from PIL import Image


class Slide(models.Model):
    """
    Model for whole slide image
    """
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=1024)
    description = models.TextField()

    def __str__(self):
        return self.name

    def load_image(self):
        if not hasattr(self, '_image'):
            importer = fast.WholeSlideImageImporter.New()
            # importer.setFilename('/home/smistad/FAST/data/WSI/A05.svs')
            importer.setFilename(self.path)
            try:
                image = importer.updateAndGetOutputImagePyramid()
            except:
                raise RuntimeError('Failed to load slide image pyramid from ' + self.path)
            self._image = image

            # Count how many OSD levels we need: OSD requires that every level is downsampled by a factor of 2
            # TODO This assumes that every level size of WSI in FAST is a multiple of 2
            current_width = image.getFullWidth()
            current_height = image.getFullHeight()
            levels = image.getNrOfLevels()
            smallest_width = image.getLevelWidth(levels-1)
            smallest_height = image.getLevelHeight(levels-1)
            osd_level = 0
            tile_width = 256 #image.getLevelTileWidth(0)
            tile_height = 256 #image.getLevelTileHeight(0)
            osd_tile_width = {0: tile_width}
            osd_tile_height = {0: tile_height}
            osd_to_fast_level_map = {0: 0}
            print('Smallest width', smallest_width)
            while abs(current_width - smallest_width/2) > 1:
                print(osd_level, current_width, current_height)
                current_width /= 2
                current_height /= 2
                osd_level += 1
                # If current_width is closer to previous FAST level width, than the next FAST level width, then use that.
                if osd_to_fast_level_map[osd_level-1] < levels-1 and abs(current_width - image.getLevelWidth(osd_to_fast_level_map[osd_level-1]+1)) < 1:
                    osd_tile_width[osd_level] = tile_width
                    osd_tile_height[osd_level] = tile_height
                    osd_to_fast_level_map[osd_level] = osd_to_fast_level_map[osd_level - 1] + 1
                    print('Map to next: ', osd_to_fast_level_map[osd_level])
                else:
                    osd_tile_width[osd_level] = osd_tile_width[osd_level-1]*2
                    osd_tile_height[osd_level] = osd_tile_height[osd_level-1]*2
                    osd_to_fast_level_map[osd_level] = osd_to_fast_level_map[osd_level - 1]
                    print('Map to previous', osd_to_fast_level_map[osd_level])
            print('Total OSD levels', osd_level+1)
            self._fast_levels = image.getNrOfLevels()
            self._osd_levels = osd_level+1
            self._width = image.getFullWidth()
            self._height = image.getFullHeight()
            self._tile_width = tile_width
            self._tile_height = tile_height
            self._osd_tile_width = osd_tile_width
            self._osd_tile_height = osd_tile_height
            self._osd_to_fast_level = osd_to_fast_level_map

    @property
    def image(self):
        self.load_image()
        return self._image

    @property
    def width(self):
        self.load_image()
        return self._width

    @property
    def height(self):
        self.load_image()
        return self._height

    @property
    def osd_levels(self):
        self.load_image()
        return self._osd_levels

    @property
    def tile_width(self):
        self.load_image()
        return self._tile_width

    @property
    def tile_height(self):
        self.load_image()
        return self._tile_height

    def get_fast_level(self, osd_level):
        """
        Get FAST image pyramid level from OSD level
        """
        self.load_image()
        return self._osd_to_fast_level[osd_level]

    def get_osd_tile_size(self, osd_level):
        self.load_image()
        return self._osd_tile_width[osd_level], self._osd_tile_height[osd_level]

    def get_fast_tile_size(self):
        self.load_image()
        return self._tile_width, self._tile_height

    def get_osd_tile(self, osd_level, x, y):
        fast_level = self.get_fast_level(osd_level)
        width, height = self.get_osd_tile_size(osd_level)
        access = self._image.getAccess(fast.ACCESS_READ)
        tile_width = width
        tile_height = height
        if x*width + tile_width >= self._image.getLevelWidth(fast_level):
            tile_width = self._image.getLevelWidth(fast_level) - x*width - 1
        if y*height + tile_height >= self._image.getLevelHeight(fast_level):
            tile_height = self._image.getLevelHeight(fast_level) - y*height - 1

        start = time.time()
        image = access.getPatchAsImage(fast_level, x*width, y*height, tile_width, tile_height)
        runtime = (time.time() - start) * 1000
        print('getPatchAsImage took:', runtime, 'ms')

        start = time.time()
        sharpening = fast.ImageSharpening.New()
        sharpening.setStandardDeviation(1.5)
        sharpening.setInputData(image)
        image = sharpening.updateAndGetOutputImage()
        runtime = (time.time() - start) * 1000
        print('Sharpening took:', runtime, 'ms')

        #tileAccess = image.getImageAccess(fast.ACCESS_READ)
        #return Image.frombytes(size=(tile_width, tile_height), data=tileAccess.get(), mode='RGB')

        # TODO get rid of asarray conversion, and read directly from bytes instead somehow
        start = time.time()
        image = np.asarray(image)
        tile = Image.fromarray(image, mode='RGB')
        runtime = (time.time() - start) * 1000
        print('FAST->numpy->PIL took:', runtime, 'ms')

        if tile.width != self._tile_width: # TODO What about edges cases here.
            start = time.time()
            tile.thumbnail((self._tile_height, self._tile_width), resample=Image.BILINEAR)
            runtime = (time.time() - start) * 1000
            print('Resize took:', runtime, 'ms')

        return tile