import Vision
import CoreImage
import AppKit
let args=CommandLine.arguments
let input=CIImage(contentsOf: URL(fileURLWithPath: args[1]))!
let handler=VNImageRequestHandler(ciImage: input)
let req=VNGenerateForegroundInstanceMaskRequest()
try handler.perform([req])
guard let obs=req.results?.first else { print("no subject"); exit(1) }
let buf=try obs.generateScaledMaskForImage(forInstances: obs.allInstances, from: handler)
let mask=CIImage(cvPixelBuffer: buf)
let ctx=CIContext()
try ctx.writePNGRepresentation(of: mask, to: URL(fileURLWithPath: args[2]), format: CIFormat.RGBA8, colorSpace: CGColorSpaceCreateDeviceRGB())
print("ok")
