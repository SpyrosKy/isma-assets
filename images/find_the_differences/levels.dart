import 'dart:async';
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/services.dart';
import 'package:flutter/material.dart';

class MaskColorableImage {
  final String maskPath;
  late ui.Image _image;

  MaskColorableImage(this.maskPath);

  Future<void> load() async {
    final ByteData data = await rootBundle.load(maskPath);
    final Completer<ui.Image> completer = Completer();
    ui.decodeImageFromList(
      data.buffer.asUint8List(),
      (ui.Image img) => completer.complete(img),
    );
    _image = await completer.future;
  }

  Future<Color> getColorAt(int x, int y) async {
    final ByteData? byteData =
        await _image.toByteData(format: ui.ImageByteFormat.rawRgba);
    if (byteData == null) return const Color(0x00000000);

    final int byteOffset = (y * _image.width + x) * 4;
    final Uint8List data = byteData.buffer.asUint8List();
    final int r = data[byteOffset];
    final int g = data[byteOffset + 1];
    final int b = data[byteOffset + 2];
    final int a = data[byteOffset + 3];

    return Color.fromARGB(a, r, g, b);
  }
}
