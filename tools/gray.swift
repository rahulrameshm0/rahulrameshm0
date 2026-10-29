import AppKit
// usage: gray <image> <size> <out.json> — writes a size×size grayscale grid
let a=CommandLine.arguments, n=Int(a[2])!
func grid(_ path:String)->[UInt8]{
    let img=NSImage(contentsOfFile:path)!.cgImage(forProposedRect:nil,context:nil,hints:nil)!
    var px=[UInt8](repeating:0,count:n*n)
    let ctx=CGContext(data:&px,width:n,height:n,bitsPerComponent:8,bytesPerRow:n,space:CGColorSpaceCreateDeviceGray(),bitmapInfo:0)!
    ctx.interpolationQuality = .high
    ctx.draw(img,in:CGRect(x:0,y:0,width:n,height:n))
    return px
}
let g=grid(a[1]); let m=grid(a[4])
let out=["size":n,"gray":g.map{Int($0)},"mask":m.map{Int($0)}] as [String:Any]
try! JSONSerialization.data(withJSONObject:out).write(to:URL(fileURLWithPath:a[3]))
print("ok")
