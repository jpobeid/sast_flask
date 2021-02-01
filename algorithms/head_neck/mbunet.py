import torch
from torch import nn


class SingleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super(SingleConv, self).__init__()
        self.conv1 = nn.Conv2d(in_ch, out_ch, 3, padding=1)
        nn.init.kaiming_uniform_(self.conv1.weight, a=0, mode='fan_in')
        self.bn1 = nn.BatchNorm2d(out_ch)
        self.re1 = nn.ReLU(inplace=True)

    def forward(self, input):
        c1 = self.conv1(input)
        b1 = self.bn1(c1)
        r1 = self.re1(b1)
        return r1


class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super(DoubleConv, self).__init__()
        self.conv1 = nn.Conv2d(in_ch, out_ch, 3, padding=1)
        nn.init.kaiming_uniform_(self.conv1.weight, a=0, mode='fan_in')
        self.bn1 = nn.BatchNorm2d(out_ch)
        self.re1 = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(out_ch, out_ch, 3, padding=1)
        nn.init.kaiming_uniform_(self.conv2.weight, a=0, mode='fan_in')
        self.bn2 = nn.BatchNorm2d(out_ch)
        self.re2 = nn.ReLU(inplace=True)

    def forward(self, input):
        c1 = self.conv1(input)
        b1 = self.bn1(c1)
        r1 = self.re1(b1)
        c2 = self.conv2(r1)
        b2 = self.bn2(c2)
        r2 = self.re2(b2)
        return r2

class SingleConvT(nn.Module):
    def __init__(self, in_ch, out_ch):
        super(SingleConvT, self).__init__()
        self.convt1 = nn.ConvTranspose2d(in_ch, out_ch, 2, stride=2)
        nn.init.kaiming_uniform_(self.convt1.weight, a=0, mode='fan_in')
        self.bn1 = nn.BatchNorm2d(out_ch)
        self.re1 = nn.ReLU(inplace=True)

    def forward(self, input):
        c1 = self.convt1(input)
        b1 = self.bn1(c1)
        r1 = self.re1(b1)
        return r1

class EncoderBranch(nn.Module):
    def __init__(self,in_ch):
        super(EncoderBranch, self).__init__()
        self.conv01 = SingleConv(in_ch, 32)
        self.conv02 = SingleConv(in_ch, 16)
        self.conv03 = SingleConv(in_ch, 16)
        self.conv1 = DoubleConv(64, 64)
        self.pool1 = nn.MaxPool2d(2)
        self.drop1 = nn.Dropout(0.2)
        self.conv2 = DoubleConv(64, 128)
        self.pool2 = nn.MaxPool2d(2)
        self.drop2 = nn.Dropout(0.2)
        self.conv3 = DoubleConv(128, 256)
        self.pool3 = nn.MaxPool2d(2)
        self.drop3 = nn.Dropout(0.2)
        self.conv4 = DoubleConv(256, 512)
        self.pool4 = nn.MaxPool2d(2)
        self.drop4 = nn.Dropout(0.2)

    def forward(self, x, y, z):
        c01 = self.conv01(x)
        c02 = self.conv02(y)
        c03 = self.conv03(z)
        merge0 = torch.cat([c01, c02, c03], dim=1)
        c1 = self.conv1(merge0)
        p1 = self.pool1(c1)
        d1 = self.drop1(p1)
        c2 = self.conv2(d1)
        p2 = self.pool2(c2)
        d2 = self.drop2(p2)
        c3 = self.conv3(d2)
        p3 = self.pool3(c3)
        d3 = self.drop3(p3)
        c4 = self.conv4(d3)
        p4 = self.pool4(c4)
        d4 = self.drop4(p4)
        return d4, c1, c2, c3, c4


class MBUnet(nn.Module):
    def __init__(self,in_ch, out_ch):
        super(MBUnet, self).__init__()
        self.b1 = EncoderBranch(in_ch)
        self.conv5 = DoubleConv(512, 1024)
        self.drop5 = nn.Dropout(0.2)
        self.up6 = nn.ConvTranspose2d(1024, 512, 2, stride=2)
        nn.init.kaiming_uniform_(self.up6.weight, a=0, mode='fan_in')
        self.conv6 = DoubleConv(1024, 512)
        self.drop6 = nn.Dropout(0.2)
        self.up7 = nn.ConvTranspose2d(512, 256, 2, stride=2)
        nn.init.kaiming_uniform_(self.up7.weight, a=0, mode='fan_in')
        self.conv7 = DoubleConv(512, 256)
        self.drop7 = nn.Dropout(0.2)
        self.up8 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        nn.init.kaiming_uniform_(self.up8.weight, a=0, mode='fan_in')
        self.conv8 = DoubleConv(256, 128)
        self.drop8 = nn.Dropout(0.2)
        self.up9 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        nn.init.kaiming_uniform_(self.up9.weight, a=0, mode='fan_in')
        self.conv9 = DoubleConv(128, 64)
        self.drop9 = nn.Dropout(0.2)
        self.conv10 = nn.Conv2d(64, out_ch, 1)
        self.s10 = nn.Softmax(1)

        self.dst11 = SingleConvT(128, 64)
        self.dsc1 = nn.Conv2d(64, out_ch, 1)
        self.s11 = nn.Softmax(1)
        self.dst21 = SingleConvT(256, 128)
        self.dst22 = SingleConvT(128, 64)
        self.dsc2 = nn.Conv2d(64, out_ch, 1)
        self.s12 = nn.Softmax(1)
        self.dst31 = SingleConvT(512, 256)
        self.dst32 = SingleConvT(256, 128)
        self.dst33 = SingleConvT(128, 64)
        self.dsc3 = nn.Conv2d(64, out_ch, 1)
        self.s13 = nn.Softmax(1)
        self.dst41 = SingleConvT(1024, 512)
        self.dst42 = SingleConvT(512, 256)
        self.dst43 = SingleConvT(256, 128)
        self.dst44 = SingleConvT(128, 64)
        self.dsc4 = nn.Conv2d(64, out_ch, 1)
        self.s14 = nn.Softmax(1)

    def forward(self,T1, T2, T3):
        x, x1, x2, x3, x4 = self.b1(T1, T2, T3)

        c5=self.conv5(x)
        d5 = self.drop5(c5)
        up_6= self.up6(d5)
        merge6 = torch.cat([up_6, x4], dim=1)
        c6=self.conv6(merge6)
        d6 = self.drop6(c6)
        up_7=self.up7(d6)
        merge7 = torch.cat([up_7, x3], dim=1)
        c7=self.conv7(merge7)
        d7 = self.drop7(c7)
        up_8=self.up8(d7)
        merge8 = torch.cat([up_8, x2], dim=1)
        c8=self.conv8(merge8)
        d8 = self.drop8(c8)
        up_9=self.up9(d8)
        merge9=torch.cat([up_9, x1],dim=1)
        c9=self.conv9(merge9)
        d9 = self.drop9(c9)
        c10=self.conv10(d9)
        s10=self.s10(c10)

        ds1 = self.dst11(d8)
        ds1 = self.dsc1(ds1)
        s11 = self.s11(ds1)
        ds2 = self.dst21(d7)
        ds2 = self.dst22(ds2)
        ds2 = self.dsc2(ds2)
        s12 = self.s12(ds2)
        ds3 = self.dst31(d6)
        ds3 = self.dst32(ds3)
        ds3 = self.dst33(ds3)
        ds3 = self.dsc3(ds3)
        s13 = self.s13(ds3)
        ds4 = self.dst41(d5)
        ds4 = self.dst42(ds4)
        ds4 = self.dst43(ds4)
        ds4 = self.dst44(ds4)
        ds4 = self.dsc4(ds4)
        s14 = self.s14(ds4)

        return s10, s11, s12, s13, s14










