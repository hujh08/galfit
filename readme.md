Toolkit to facilitate running galfit

# Introduction
The most frequently way to run galfit is to feed it a formatted input file. This package is developed to cope with this file, mainly creating new file and modifying an existed one.

# Constraint file
In galfit input file, parameter `G` is a file which gives the constraint of fitting parameters, like fixing centers of two components to be same.

There are different ways to handle constraint file. In previous version, such a file is loaded and parsed semantically. The constraint information is followed when modifying the components.

But this is complex, and is not so frequently used for photometrical fitting. At present, a much simpler way is adopted, where treatment of contraint file is indenpendent on the galfit input file. The constraint file is just a string, like input image, mask file and so on. It is not concerned what is in the file.

In current version, a compromising way is used. Constraint file is loaded and parsed, semantically and optically, but independent with parsing of galfit input file. Semantical parsing is helpful to create and modify constraint file.

# Install
configure: `./configure  --libdir path/to/libdir`, where `libdir` path is folder to contain the package

Then `make install`
