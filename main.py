#!/usr/bin/env python3
"""
Sum up 23 November's world news in one image.

Deterministic, offline generator: draws a one-page newspaper front page
summarising the world news of Monday, 23 November 2026 and writes it to
/output/entry.png (override with the ENTRY_OUT environment variable, or
MAKEFUN_OUTPUT_DIR/entry.png when that is set).

Pure standard library: no Pillow in the grading sandbox, so the letterforms
for the frozen texts below are embedded as pre-rendered glyph bitmaps
(4-bit coverage, zlib-packed) and blitted by hand onto an RGB canvas that
is encoded as a PNG with zlib. Same frozen data + same code -> byte-
identical PNG on every run. News facts were compiled on 2026-11-23 from
that day's reports (Associated Press, Reuters, Al Jazeera, Xinhua) and
are frozen into this file.
"""

import base64
import binascii
import json
import os
import struct
import zlib

# --------------------------------------------------------------------------
# Canvas / palette
# --------------------------------------------------------------------------
W = H = 1024
MARGIN = 46
CONTENT_W = W - 2 * MARGIN

PAPER = (248, 245, 238)
INK = (18, 18, 18)
MUTED = (92, 88, 80)
ACCENT = (168, 32, 24)        # newspaper red
RULE = (30, 30, 30)
LIGHT_RULE = (196, 189, 172)
CHIP_BG = (238, 232, 219)
BODY_INK = (40, 40, 40)
CHIP_INK = (60, 50, 30)

# --------------------------------------------------------------------------
# Embedded glyph data: one packed payload per style. Each payload decodes
# to {"space_adv": int, "ag_h": int, "glyphs": {char: [advance_tenths,
# width, height, dx, dy, hex bitmap]}}; bitmaps are 4-bit coverage rows.
# --------------------------------------------------------------------------
GLYPH_BLOBS = {
    'masthead': 'c-rk;OY0*y68|nf`_O8==eDp5IRpYB5W*6IT9T8)9s&b_5c1vAZMWTeRF$f;GYJHXxs3n6ZcFuk$-iAb{v2ZdA*5d}AB54@OZf4JpDrJ?yIy|$->*Oa^zriHx68jSAO5SXy()KA>N;J;ikteCZu?p$&eFHnnmPDz;4K3#@_|nbytx%ijq$O>`ypIz+j!yg5bsu$K8~PA_`IFc-?%K;i0>xFW<hvB5|afR@#B694h!u5M#*HsO8hKpF8BfQm)94KS>Rt3pKlx%<l}V<g9W<Su3@lXDacWXwIzt30JTX3@g1a=3YYx3Iy}jOjrg%4F2#cF@22>FA*2Q)z5wkI$b#*Bp;I-S1<Q?CmNYy4N+9uxr642gU9)gQB*8C@C<{DzD2uWngG4Kcuyn+a6G`N`{oK;N!xbNI+FHv(FQlnC*MbUR&w_->U@4@&`VihuDWtjj(m?owh6Qsbj6kuWxNTu}JJWLvu8}I^mr82$Vudb0Xjlfw>3kM{`TlzO_cN|g+dpv?=6Z>c7UY~_@J3QDxO-+XCF!+W;~Wa^XH3M>s$o7<B+3pU_VeV@rh*(ZiQNRTkk5I5o#x}!Ner+hco|_Qm3uwMu%#UrBkbIJEfiZAgEYhz?o*DiqO;pLws#@~Hnh4-U<*AKBW!m#0^7N50;}4fhKDtu39COP_6!}m41~bi6MXBUUY6{P<t(0%-^|wwc|zap2|Z4H`=I)W3dP3$a}4`3QCW_#2UHF0uZ|G3P}c07wZ>RixQv$zSp86<Lqx;#Z>xjT9ACKldrPOY;<=zdZhrbdo1a$Gb^9lGKb>yll`A_+<3|3uij+*{oA>4Y>ZI@Q$U_;bb2btenYh5jStd?1agvD>YY@f3O`}-l)8oRjaB!Rd=HN6F=a{&Kz_shI!exJ~%sfY6;w%%Vm^d!qCS&d2B7bLb=9%OTaQ>N{4shw|_Gp~o#8tceb8wCmPwlQnF>v`6Y=HLpZlc5T@P2aW2lu#)<3F~TjETGZvoBVEriHxfkw4RD{<@yv{1e@obM$r(42)Y+<KF$Az#1ss>yofV@Z|T1;KKBN;{C)w=?QB6eNUveT<exM2j5S;pE&sh;Ri+M2en&pU+a5cYsFs?0c_F7m(Ofk9MMN)c9$kLu*;`&3@-u@&F?5aNd)}{zJYJx8;AoVqv-z3dIbk)IPI6c4w6{F{Q8^*DpvJ=&$vAYn2yFa37m^oUEv;0vFw_5@2*f!%&c2Z%yfF@0>z_}{MDX$D|1!)DuGEdp{!qG%Iiu?u$pj3!YticqJv%B?2%&!2@J%%u*n-Gl`aDIcECa$?FdzT+v^1qZpM1J?^<>gj)26q@|OFy#=?lEUSX4In?qpRCbYvG3mG}cruPL6O0@4vO;Zi+1k0*j2U`?dG06|cl2q08O7x6T**liye~`{f*+*A5irO_5eBWmzh_aO3WJF2I@vkr(ek*6Q&Y*9_uJU+-MJ&UiG#Jg;i8!}!e~KpO=xt8%Ql5|#SIVFs$)E;W$B-j=wZh#g-H`)kx_VYC(gTl2cXh6N^oCT+fHsE#1CjS{mYLAw-uycJ<<Or3M#Pu>E@yo(xCX(6Sb}~hwzO60C`V}}rM55UnH@wc*s<q;q>wuFzSvT^q+GM`n4f-L383%%buo8N*6G)GtS@nTrgR3L`ck93x$Dns$_eJZ&rwDui{Qk@(&Oa~r2m#Nc|>AHix~kd#>|LfWB7phMGTK^2*Vr1E@5~L){#CP{_K9vp7$(06XMGdyvEEt(#K7${Uq@ckEuGmkY<5LddJoGY^D=<(1781Cuslo(D%spmyh$#gNq#<eQZB#Nz*@)Gw{H?DtWB{;P2tovt;G|iHH(Fdq~`_0p-o(5fLoU#R&GyvbQ&ksH2%OroI;?=$fcwdsPz^tr-NEsAy%qyv^`Xv)Oia<+7}-o5?d_h#GmbqkH5#!Z-IT?iKZKo)vX@#0iWl$1{-se9*1texC(2rpW8;w(i3a4@wqwrZyIDbA=5W#!$aQ-5Bb2s2xMi4%K6*-l1{~l{<7EL&XlA#?U*g8EM3zz~tjR%=6yRH}nmCL;nnvb?w%;u1lR3Z=rY*%T)gybn~d+t{&Bx>1y<T<9qd}(6fVk(#`bt|NR0RQX6{E?do!@E(O!Xm7HtjFV}m-h-7T-v0?K9Oh)q=Dgdf_yEAbH1LUuJxIROLN92}CyR+0l@q5b>+}YeFc10lP;DT%Fb7u(`PZJWfsurHG@L9oWeQ00nuo|leYnWALp#g!1i`8X5>S}OXrPjl!I@R0tc%3*PQMRu3rHKN$=taEJ69?AWp&Q<tyyafT(ha;Kn>ulRXiUeS8Ogc(JKzi41hGgCE?bVx4{_<vwjeoqmmoh?wmI9KHHPkgJ@h2)-_%?q)TrN?>+DcJX(ehh2E6%SUo1Z~t`-sE-m)#FuCN)E)mDV(6y-FgD>N_`<aI>jsqAFk4<34prxH}90!(A9R6f_AOSG|_5$EiN{vFJ!LC0|;e=?)G&Rxp;!u8%6nTyrXg|5*V6jIU;%rGnBLN>9^U=Rike#pgRjy_Q3Ip_=?`-2(8E(z-?Mxvkyn8t|7`S90%B(~9=jN>pYVx;ziAiCnX!}b=(5#UVrE4w#uG4yxO?v)wMd1|-}ZO)-}dxPY*<qOX}3w!jWQh0n^G}a*+s7AvisrjL;qk7`yvg1czX>7u8fvIpJL*>q7*p7RNFn-n7YS>~#xN{L<suol%$Yn5d8X#krFtsbGDAB+fqT)h@h&>h65e&^^7ZS1f8K$CnMv7u&Q+EE7zl73I(cT4<{5h(kJ(KTER?RVxw>@HwOoPlyfa{+nTX>d|o+5!gWMHJhk?A(y=r@{;E}C9sF=v|#ZDv=upE5Fn5de>Lf`Pt#|NHNM07)wZe*',
    'top_kicker': 'c-oa!O>5jR5dAMcyC7MzZ0)U~9~4Skdg-B*AWNF$&_f_lC?Ws7^JXOPCfPJZEbC``H1j<3W^^~)-lSYFQ~5I-{4x&d>hgLx*f0)PzyID`-wubn;mvUPIWOZpy3vf*j)NznDt|`S@M|32vXPzKXea#4=*I!C7NX6xm8n*%&{0Vg6t5I#%8CnlQ)vS9@SbP^juefVsQ_2f<?y6tUX@l@CcF)7WGl_UeD$Go+$e(PMW<<nDQISRt9A2WSi~Ri&v0sNVfqR=LWiy}_pCH(=-Uc#vt?$kK_(pbr!;q4{$lk|^P(Aicb-};+pNherAju{+fw<9o8y&eYS7Xijw3Hm;Upy5wrUjy<nTcVM3%sy_8!zMQ!@{<hUH}&mhZtj#m7ijHhsrtUfR(-$30pCoe!X6{1~6G+4`2WdpQSmt=)L}ukm951|Pw|ad3C4cApAYOJyBJRI2{Kv8?pM0*PxwtZ9~7^zLB6L(`@=h};zLoSNB|nfb)ev{@`}*mY#r6BKX^T7@d;)Vxkg`4dy-4tFOxTVMQP<L5Kkenq-o37Rr?v4Fvsvz;NyB4Pz=Mg?-qcbFtk0$G`%Lm49qc_^$MI;vBH-0874I92KpUDhFw7P6rB^;sck_vo$@A)s2^y74H4$X&P#0l@7-V8NW;gx$;mbRk5{xOsQIo&-&%3!$Xm%-^1A=33Z6p8=%}246)7IziK8<Yl($jyBI~S?!B$-4W<~e`X@{U<_RllD^}tbH`EUAB?hQyX?c+wP@U1z6ahQ0EJxLrTdNhFhq6bu=oLLfzuTB;$~D%8d`#uC^d*$-VG-i&Ks_Nm7zOZl+RM$_%fkKGe`6kR~DowF>;OgX6DO&%57-*!ltu!Ih+-~$ic`CP}W4No`;bN#tI*NLJdN|x3WUoDcFu_C>9yNzyAm1fG)!',
    'date_line': 'c-qBR%Z?pI4E>khu<1p;AM+2eVi!<U&kRxm5h0PHDF4o}UEO^%nISL&(KET@x?NR1wvQkAw7q*<+IU&|hwaYWeJihC-fwq0?%S)^AK%`;+wMMX-)(m<Y}oDYcD4I`Q!}fPRL5`Je%`ko?{Svi>s^O^voqmWrJ%c}4GJ5y3cFUjw(AaMavv=yrF8GnXY5yL7_2isdxfCvjGDg3GYS?g^=fAjsa@Y)`>wON&q69gi;lv(_0mhg%#*-qrx`tlJR4oXz@}4yRr~3cJaJkP%&1G~U9;du6(Ni)ufl?>>{x<oBk*I@Tu&xo_Ay|#EMS&^l?jEFbrpaJ{!3tK0n-64Ay{)BN<%CMB03RumP50s(HS|M>1T@}4Km!3-fY-o;W1z;w9%7ht;HwugyndIW)K8@*xC-Ih-Mw5;O^Oa@NvKlRz+|S*CUi=9Kgh|K#{K_K?m<iee|pu*!Kj?r(HV&rU_V>hiVw_!fAgRw5khDue1u{E~uxK5&x9tc$El-9zj-yK*XVCr5dblS*;cRS<qyy)QG98bCp|<*UC<I?ppCZv?61EAY*LYwYf2-A0#qiF1E8=nB^iH@tw$?=_ayJc*&X~v}FACr>t7nrwk|fLq=fpDXTs%+0AJP@{a@=$uE$Z7-^o5vEX=|ji}Bs(X$+6_+Mm#Tn;X4qO;o57fFUJYu+XHv=pW~&TH}{D`M?qOcKjX&YA*oDG)L7HMF6FJ+Y+;>kU(1x534;E)bcSixRq(L(N|bx{OgNtSupbuw20og`w%0kL0PBaK7RS>aiKNx`3>&-N=Q6sox|y)qKZEF8SfUB?aVUBnc_zd~J{#Qx_6cOVM;j7#wb;^)}%|=M!CS@u5|^InvE5L&gonGj@hzmyXayVtM5ffXkJXLBzxyq%39@$B$ial{!v1R4$ZR1dS^V-Hd+6-g))FJFFTNuu*+ryq@v04SL+#^|!5#gshcib@P{xsp0sn79G)JyeoW{1Fep}cK=*bWpKbksL2y6geOob%mE77{7(hK^b0UKvzrrA9U+MwU;og7*AEYr@$?TJcyrSN5E}|iX~+`<&Z0pDReGf<Afe?nvWbivRQNG0h=mffnFKjc693wYApUv<=0dof-v0xq|Mpm#SY$f4>y;+$N)x}z7f87nin4J@XA<RgBBFUno#gR{Zf+}0-hRnJXvVN|7Olul|EfdJDq84i$A#Z!H(~l6n1bEIjrUC(<oc4ZGjZWI{CS;y>XR<SeEcGN38#2h(@atwZ3-xV=*==qBuej<#J0^*r4QOzW$@vuRctYfG99(YWtdFkXs@2t{UMV!cUgr$P`5b3JqRNnwojBZloJ`pp87N#ZW{b_9WtfA|B9QnOO3M65HNohrbwTbYhtA-m5bRb;UC0zH`H7W7SvyJETtn;jtBibxD{&}I{eBj)r+j?jqIRt&-Z-HoX3D3Wq=~hA1}@BfoA9BKNr-pSb-tU?5{|gITspd0qnGMP2Dc7>8$6T&MDIz)8{ex+H*WFvR|Vd$yc5V)JfEz-sAo#Y^5JVL&{dCs&no6{P|Ci<8A@',
    'kicker': 'c-pmA%c>kV5dD{4_d<_usdaZD2}#J4JP08%Mz69LSr|+L!T8@(r%LJ>&mD6eaCC>unVyn#RCVgK-Yl<Q<=UU;_V@Cz?dy_XJb$@7SVk}Y{O8rn*UQ73<&)*%cWc9H9X@9D>tc8mqRr^Ay;B-EQ0jf)LR%R@9D<)lNH&)G2-%IP5@b8cND|Tt4+$z15ZO40LmcqIL4m5QuyN4xY+XLROEcEqYm~rB)LN%%F~9SUuF+vkC;8cPlqX$YmnCx#U&qY3t}?@@YgRs-F`4(Ox)&d&fCEF&{A|)R!W1+cAG+7W;f$^DG+wA7FE&%Rf^hPv$RsKQMXHZbqI}K>bCqVVSLWSXa!TiO&@u6r4n`3=7>5~)OBwDV9sZo*o}8g^<(x}G=L^tr`%Mv%z?Qe6IwTf_(;}MC(piYx0zEF`j;(^m_{^yaJohk~xqu>q;)dtvUQ$Knuxr-7yjR3sMHW9Cjlrn525rXwz6$7k#dNrP{WX~<KbZLSJcqqGheJ|SJq-;BXjR&PmBk@2l+lG;P#W#cpmgPjxm+eUYhNW=pzJUdvBOHnkswx3`-Z8dV@<aSzEaW011d&8E3$#Wx5$n6LyEIAHf?)ig@|lC32sfAumNXitM&pMSeKTvVBZU$Gzhk(b6Z-)k@jAVVn>D7Rg6sfi4SUK;tiQDO7pvWQfz9HkXW3kcRNtl?unq(ts;ByLq%-WRuO!5Abyw>p+^QnA_j`2QvCk?4SZO0amMbaV{#IjnN7&5*v|$ol+Ffb)4RgiUB#Go&fP`>Tb1S5t4Zh%7e0my|L`8$>vb1BRJK#L0F_8$f{K`$J<)iUc`H#+o9;@zZ01P=oCtJ&yw``~)7cF^$k}vN+vvFTOS(LbXKX!PInCX&H0^A@lVQ@>(e?Apa%fQdX=ch^6%@IYLn7ZLS1G4>rpYa$n)7sApdP(KC$Ap$akD3Un_;e~W`}{BtxC~E^t^iI<Vq}F=kg{1wV%}@w1&d0PD@Rx6#l|Z9p8Bk{7(pMetD;cnyBFyXt<9Ci`0Hxi2~~6jG8Rxx8r?<Biq!pLZJ35sO`)voYZuMDi^Gs|0mH&m$o_xMpaRX@g9tZ8_x2T3l}er@_HRhY#?=9<uV7=j?X4K!zGUmk3-@x%H|ma3VE7nWZ)^Of$%N@dK+&Pc9f>KwlrmtMG_(e9P78o(hMr24e6+o2&4<&Eskl&gR1#s`-@X|>7quyIh85KdbwD9C<L`X{^E@y^V|K3Kf505vhPk`y(7dK>pA2|{FVcM7V;8@fWvm^@XNEeZ~p~vJ{ep',
    'lead_head': 'c-rk+$<E}q5q_6GD}cC@b4?Dp<Ou@9;MN`oPGV#d1BT&uw@4Pr;-a3(*awgC3w>x+l_Zk2f8<Y(58qoKzqa9r$2&sA@vz@~{r>TepU2~y?|%IL{fEc9pB{gHy!$(2^q~4+=Rprbj>lOq!j<(Q#u&Uaij&4TnTgNw3I?9B<vuzsg;X}=JDOO${Exc5h&$l1^147zbg9fE@YKLM+4ITH6TYPe)=3hNmN&+8y28aX<uNn!w4*1?i=XR7VX9=qlh6I<@@osv?|3j2x8vCtJXd)3|9#H97>jx_2mWI2w`)eVs2{ZJ$81t!{vcTfY1>HkGI7&wg3r25Dy6_=)A+Nxsh@3-nQjUijK(P`gfw9o0nwAqUt-uLny*+b^S2*g9gn|&e=(ANXZ9~Ty(T@P`e=y@&-IF$F4pFi(#AJ|Sy^SxiGpD}vSVKYezcc~-S~RXt^{z<g<Vb6+^_|<x|L0y$hcPa8Bhq=u(2;}*w`I5Z1CK0!^RGC&;H2MANlr2Ms8ovTfJVjyG4yJRl;8@6h3`p4iJ~kjWPKlJWXuo$1DME5R|-9jjkb)+&j_J@iCMmC-g?rU2r=IS%O~j?7t?@7FXJoDRUOjX5&kBpHaI`iboc`%)0hHw8UVG+fH8F*RBUzu?enm3e;~hznRSL`W%@nZujeLoqxA7%?Ig?5AJ-~1XLyjcYaDtNb%%vS3Kd2ADr#u$x^ZnFDAoK_`d4P(Z%7=xfEuk4PGpUJ(b|Py_6x*xGURYqhnFCsW-22IlqcZ2<~#sVPYrBQQB>3B%C|ZO60g$k$X`&Rn;tyd@EY*i1v)A??m;`i(Jc}s^PsT=myGVT^`ztj-62~{2Nh*)=R<!Z$xV?C(82kSE8bst*FL(CtAx9R+j&zD7d6$O~bdMb-i5c5N}1hG1q3~UbIGl)<52hRy8zBcp*BMLN7#t$3I0>j<MsFXjX%`6HURecTEaA7<63a*%pYR6IBhc{Knsg#wt;lf2!U{ijek-kTjtb^q}M*2R$=Z!KJ=Buhe>ZE9OuR-{PI>BqPiXEn=**_SnT^91C@znlUWWZJ+!ZR9<I+sC-HknaX2n_ZY!%2ur<B+dnc=<yzg-I?I_V@o3tAifmPN30pPW^h|Rp-cndC;BBG{d(Ac&-kpypE&HV9lOMzkT26sVyO6Oc=&vtRoAV>AjS)imLMq4-AO$Xy0!}3|k>rpuSR(lmB8t9tqGHt`MjAF|Ay?>RBei+g=8G_RvnJxWN#kY%QCSMuUK&rWK7+q(4<ZV~t6JL+TF{N)GEkB96z}vzRaTShfJFxj0i-C9g5xr_TESKw%DN1^Sv0AWu|4iZ&{*uN7NHVCYg<T^FC{r!%XJ0|Bt^T(r|F4qs;;=yD^P{GO${eju?W}_<tXpQq^Ah4z;IN6HxOyEngCBqdU~JqB;-N)!RVzYbGg_}NvXhZ{SBn}rO@4H(8ZOUqOUe<0ZLFc4?zGabX?(=gjML#a7si(r79jLhE0a?hd#K0?r!MzjXu(4%{Qq76RzH<9>^^2fkJYNZ!fnXR3C&kw@BV*y#>$Ci32JGqzTYgSm-6uKn&nMdU1Zng<W%WNBf8Q-_R~^aG92CyniIM2zHRG5vIqVs$NRK^G=PPYsWCkhD0Z}@!Ac6fS3@>`D?B?biukBU;UmK?%3Pi_Kpt~l7M=K<`k&F$3%{(4pb|WB{9@tnvxC^HY|qXg_WXFvxeM$H@N<pO)MffM0?zd`M3YS;s3f_b){N@YOkc0e<na(vxBK#P&(8e@|>ZeERv~tfN)U5zd2jFzRZBMs?!skyHRK9a0z9QP_%*)3Cxt$sftUs_c+)njI;42RbfyJ*L<5gz~Itfz7#s&gnr*bLt!GT>AM8`HIRf4RZ72cIJf8=xc=2k`4=8iYS@iaj5Ta{t6{(N8us565F=9y4sD>fvV#r^Z80ibL`BI9&my#ow>+#GoZ!2rlf|edY^thnh2G@GUbuo!6c=gYIkfHrkuuy}*LrFzNp|ntetj6HuH)R!h{Rs+$L1}4l_Yx8xSnRS@*NN$IfVspB-&K|&jwU+!!{zb;VEUsSZO_QC0p2G6^`vB&X7MtxX9g2z@%%Enx|adNkPI=q6e$#@P&k8-xo=ewgzQy)o^xYKpT>tKBN*-nS;pD^RiB(cP2X?M=|y)KT}loS1loI-jGR#1#tJJAC?U%G{<DcEL%$h_d(2fUPe%deTjNj$UG;H$FothWftTkk8M2m1bNG<Fq~X*dfb38y2Fj>LsCDZ=p&0n=io*Olh?9bEHwl4R2r9;&xpFt|E=xdwazkaii+9}nuf^t$<M&fjI+&Wk}9I7k)Gr^f`#%VLIALxAVIq92>b!=<pguG{jr>9xUvdC$LP?0nRGSbB)$EwRw^R-$C>?u<K1bBZm30j>crr)NdvOV-WZ?25O)l<FiyNvJ}_zr%r0+rm?3dM9AIyQ&RBtI*cwxEuSU_fp2$}6W369UIUJd+L=PdeW^vti!h#_grweeJ%a5D=1kmvj14_37!8NX#bsV;TSzQUeIjp9K4gF^Nv7<@6FSJ;9QbT?)EE_Tc?T`**RO89mI>s=b*?=+n`P4_<dJg-8ylM+PE=O_Y{-ksnBikNz-kdE?W0c!d%yEyYnf(!KwjqZR)(1>L%-d!Gg#B_FJZA$wk%LZ2LC>Gs9!XBMcCdUsB>3~szW^2UcR>',
    'lead_body': 'c-p;KThAmn5&bXoJfQa7-nWQ6Af6D2Cx{|ncL@PjED4ID{C7@O+1;LelT9{RXpLsdJ$Cujz3gvq@80IxKhN#!+bb9ExBU9^H@8;`)ax(5dHd$w?bWxp`|Z`A@t?W7ySmd~$LRDi?eOKO?znw+zx{em(sPm;4IlbT;V-4aT^)C2@vjGm<8Xaw{2VHeN%dy4P)Qw=!t*gH6Ju;6#pwK)Pa=r=8N^U~uO6%Fs4=yXk1!G;ZbPTWjN@>Ve;QT@)!QU$H%#c(<v-VD75Ef2i6oOv&y!Ilc=SL)J4CY}DuQ@SEdpaJPCyj_2`FKrJaT;mcN}GDM8~;z8KX`qe9FD~HC2^snHgybX0S&cUX&VuTsEeiR3w#QcLMC50Jc-24rO2&KiKxvA{26N8HYJe<@(&1F}CcyT>*z^L}4dlJC+s?jTs?`+97CVzKVWK@0mD|^g01B>5l-%XBsAvmWF%szR(s?wyZ!nJ&YV73igb*sx^Bk&qmdS1dgmwa0rFyEOTkurq;1**ox%gu$`B&hT(XZhSL+TWfNqx9HPVZ(unL~?Pz^!*3M1c2=kpEY5Gka8EbQhEkj4NVRe>S$UJ|T={G9y3J<tYP7WC%FA!T)0`U`qXa(QpwPdNw=FkR=a1K;Y@eEt?0<(hTI2v?N`W!g2f?L+FeNA8u#?7133Z%^JtN2~*ie|XwIuNBT)?^fWZ3{D%%NxxoB-(FCG^eL%E3FywsG9Bc+fh?0oi|RSG7I=a0*|g%z$fqzmonI`uBQ$4gQM~=GoD7`ZF*lyOj$wD#+X#1&^clsH8V2iXE<;Z%^=Y}eJL78F3mBbtp*K3RF-Uo9V9Dz5Ej_x8W}k77NEWFqdL?!Y7e7_nGV!7YB2D*dnJQSWQe&WZbq;tY7*_YOEj~Ime1_tKf>U8Flb4h`cYVK0}|$UB+TLN=^?m^Bv=GyjAME9FD88BBsi+&L`2mC@eW0kn^76cnic%}74iDfcgPH3*(YWcjLXJ(#FN&v!=%wboHPtSY2{E*Pc?T3o*dG_sfQBq!8F1D!w<MVIX{<yDL~9!+-*VKU6BkFw~>Ds<>4-;jg<2*pQ-v-;>@}>XKKmVYh9S`omZr}ZN#C!?_OE7KQ7CdEn!&{Runid2?UifBo1mlq*p;Xa9lwphJ&H>x1|}R6MLm3S13ie^+H)xyS`;5l^${wBD<V<5QDh-qDXrbf<vCdNZbXKg!$9UICfi+ivO>{Lrki^q@f(1B)QIv3uy`^+{!b2X`3*46>?3@$ANghk!!T+a?*MPaR}GK-et;W$ErN&897#3bj~)So0I{f6-O@IV~Dy571KcIL!$-&b0c?Jy7oxW%GP60|L@Qzojux*QN|-LpqY;&x4<1t<Q9Sab=Ew%)?9&(?KySLs}epI{A%zS<23Z#gTU6A4+-q4M+Jc>Igy^w)pT^_(!ZIWwu&#zk5fzh?o@I+-BhZqrq+)6adR(w7zWX{Hqrrvn=Q|SZr(>4#7r?nB9Nnxo%-;^jS8A=J1s{Y;)0qkGCsWB=5pHMRKqQB@~LwZYI!&6ln8v^z@HlAlTfk3s7yzkM;Gd%W>Z3~;n~3^HLk8}G%t_c6n;qe2<Dnq>0!`v%-y)xCqP5am44Hut<)_xs0Oww>?N7pg3_l!vU676eCRiA_xgLrWBJJ-SqCx5Qe0*q^5ar+yHuZ_+9o~Bod#hJmJFSm7=-<KJN?iR!|}0<qn?uiPO)ws2g+*O-u#kSwT@~y#cFDiV{6809eT!Kq{y=$fg-Sf1y~#IW`k;c(P!#-|A*!MLResZy8lXvbFkh{KHEw1XMW){XOJ_F(AzvF{%uP#AFgG-1}HPodzE(}6jQpf%5mP92?r&4o|KUNjO6mUV)5fZ6wc*5g~CZRf&KEOmhDgfu)KdKc>|VvjtUBiC|TE2WJrFG6`6JT76ToSxv4?QW++_O0|!}~=f;Uq!aZN({689#82{LU;}YX^`uJX_cOS{=|M@Jv%B_i)CNldluNZ<T>r9!{cFgpOvbb^z-E(Z$2HV_|gP|;)9MX1NcQo8q5TLi;OBn!kmDCqyJ3p3f_rYbm%(9Jn=N>;TbO`Lf05;GuXBiMsBi$CDM25(1qEu&rCX3(yO>Eyi>l(O0OB|KOqXt9%CLMUStEb{v?%7MGHmQx#=5>M&?S!sJGSURoO$MwRkiO||kP2N(a%}qdS?3HO1cJaRUsIXk+7?V2$!RXL$B%qF*1j1n08i?TTe+`ZMnIA(gP)&G<&#3sD<$3bVYE~<`peGpX$ZvEOW9WhtXm9lnys~>>?R$qCyufK9~Jl}O37_086>ROH1h@s8jE_JS85BZj{4Eg4zJJq76SC2b&&8UATe~9>7%28*StORNAk9$W7WAn7-B_m?9e^XD!eR>+UO$}A@NevHBSJ8p2VmMxXmzD;J56khw4b8(kZk=U<;lZ&+I^<_pl`3c5pB<662dqukKN=>C`LhR8j<ch{Q=Iy=v;Ire5ie*o*tpw9?k)n_6c%WQOw|xnJkOa$V}xvvv0KhE9jPX3~wO+5-D8Uum2bA%TW(YIWClzA?OwXODmO+&=s6yZ-_tT_A)',
    'chip': 'c-oy;%Z?m34E&clj{&LmXlZXrE<q0Yfxs~IpzH)rVr27xVff!uMX7t&o;Bi4V?E;ZNMwm*k@Sbl{kziSRq20U?)-kel-IA`T<&bVUS7X_|L)EG<?h49UhaO%;hL^?yV|S2UW`d&cw@FUbZtH8nyk?k&$HH2>lm$;KJ<~x%j;#EMl+3?X>@PW%VrEVcNt<g5pS%FT{W3DlCGPKplctEtHWxsdKs0glaX~}A5~X?myV~zX@67#a5n&KIsu3Ra9uW<TLAhJg5b3=8Hyagr#@s_B&G=x9&EAq&Db`I?NgyQTkbI73;~220CmFixN56-9889(PL@C6P^f6|3mqwAIGb}Y_PDFrM?VEm{P?Lrp#s3S)b)-8kiHNCT&fHyIJ3b@;KdUJN5>@m%XG0bwg5uM&r!I!*=>xCN8x9g0K$6H2mpJaOr2c40?1DQ0K9B@hB;6TbVi!<L3P6T6w0WZs$&uWZ58geMI>k3SD%V_RdGDNaSzfjYq+E%kOc4z0NBlG;-3(R{O~5TPQ*^pjb4Ceg%?2Dkr&?31apw!%FL5YYhi{%R^~ark%mW@C}l#8*ko5$WA)R2^SXrj?E%xC6m3c*sbuHqst@NUMKl=}TgoYdCegITz<3<%l-FJ$a|g*}#PjV4$6gJjDrn1t-#zKUP?=?Z0?;(2OW;;i5S!_SBVSAL8pri`b<yGO2l?@y^K62Js5+@SC?nOD;`U`>Ak6Qd@?csP?eoOr`BcoySI<&LXg}PNfY+G?G=c<+`P*}a*s2OH@@+yrLt+e35@;P-A^h>l>~gc%@RIcuXBAShX!fh<8(A?$&G#v4wOFD<Em<NmBFhp{TMv;f=Mcex>6<crV-4J6uKQ7;SRfGWo|=LvHRwH!d1yJl%Jd<~pS-7}tYS9P^{w_gz#i0_y1CXP&9x&Gr?pT~tQ;9C1zo`zZ3bELnVbycXX&ccPEz$0DiSg?w8>Rkky|VHm3?O)lCpGbWM=aYooU~}Vb9FQ)7+SaMj47dJ@Qm31E)+}{fky!GpfeZch((-Q2L5`3eGN7qpV;_$>~Af!mEw#lXnmMc(%^7aD<eHdu#oVDVXVM;L3S6PXLn^Ca|9Y43mg^lx%w{K}+rar9U40WgbL2#OsSSrzn@^>2pMQ)(3j}hPE3V8i&Gr`vkoI{Nur2>F@v!d2*TlZX<xd+4v^K!d&U#UlO>E4Y~8xB&N~wkw_i*o_^5zK|TM!zY)`KD+%%=NJzH25sjc{boRH6tZ=i04YGOvdO^+n{*Y^DPJ@8bl1@vb7B*-2I?w5Cr3@_2R70gG5ATf5P>w`hXW1lG->O)Dz+Q~k_~=$iJZqAmRe`0v-Z?Q&thb-kbbrIeV+KThOUf$k?74F&>p2qbrgNHBMe7rYv9Z!3=^56VG8?UBfvqd$|AdvW120OfK?1{!4vc{g(Jm6uZCi44W_a?mXo(awG>e)PsP?bVqpM|uoc%f>PHHz^1#Q}a*cg%-hs?C)j7Ky7(2N5c=%*KI2qDsGP_zzNz=JN~0mt;CC;UMDf|O{j1G+;&EZW68>U_s!X1dHm9&yJVpKbO~gp+z^o8+8pb%64V;$5c-osbCc{n;aqI#)C{tdtnX?4ksNVzg21I#%)ri_tF55e&%cwBW&veheDNG{2ukZa=0z+vhB3>-v8P)zw*?FE2lS{1-rWr!o',
    'head': 'c-qxk+0G?55q_6*eJ<L&J$E34gg_`_5dsuN-a0{K88HwPqP#n<#ao{<KY^Jnv_^B<)!lY&uKKF{e|>xNI_COOEMMMUS#!U|k3ah4_DZVz?c-0sdi}|p+pDi{;`Zv#LLGO}{<*unyZh}p4w=q)z~$?Sce<P>-6b!X)~@gIPAJpvvQ`3Ffh*iTyx&Y0K!N}Q1Q7j&)IQtpOU5g}y*~Q&?e24~wImDoDH!7_&PkVQ3-~_B=UMuFY!41E@jjhrJ&MEoCPO|7N~qf_=EyY~4Rf|>Y|N#t6;yi)BK`zK^!_dah<LD#;0o<qdu&&mqD{SC<^-BrNhvwd-$Ie6l_xMbFJF=8#@x6{`^27$;EnsHBLNG@A#>@HyRN+Ix};q*_M8`MIcI}cJiF~x7Y_7W1xidmq(XXJV_(^^?Cx}8@P`Y496VX2MLnwar=VJ=&~-ei)_1m=wLNN0z`V&=*bF3zVeJjRIss?bE1|GzIze>xF`;d>Gs{k(g@ZUcAsJ&sWzv{bv!H{30@{@j$R%GOux$rHk$G5J^6(-LKMhsW>TIIx7!>)l?xTJv()F)uiI(2&nhZmebNSeBCWo25Z&DrwKiKycO1=p8L_6I*UwkJ$%u}vwi3ffhJK9uh4`3*}CE)|V$r{RD9#1b&?ax8ArtN(*w*O)iT&CO1TIXxnS>A_fABJ@(c7s%XY<{aZC!Is|l~cd)?cwBZ*yBGAQKBf9XXo6)sFq)VS`NXP3)LccZ`ZbM<qUdocl?ldotMtvsX%~VHUZ=z?@~P2HDg3RyXsLFWF1+mx!9@Ein=OMl`OBC)isH$y3LH9gXmC!I}xHs5j(NgIzsg%YBZL+E)<qXKUsn;R^^3=89rYn(#vA|cB92skAdA?+t%&+#28J$p_2FfY6<-A60g*ACw$_wKT?9Y5JcSrWV;tTA=V}Ew>aWzIrbm}1_8zW`Vowf;^N3MuuX-XUeG2sBNwxF4ed>R=HXa_r1Q*?orGJ+Z={~vR}wPaq+LnqWO*l{FNBSRf%=RaiDUFeLg%`WFfm+6z_B9ft(aC)eNs0tT*rAI^gwSP0>T3p86c@!(GC4foKdgHM7(`07@YO7XBH{KyR@!{3`O(Q6W?)s*>cYU|8E{W&`+qrdYYPYv5pnSVs;o{u3tMkoutwu_)Bl8@r+3Vs-+@#0nXZ`B8}R*lnMNy-?k{-ml-xk9G|iH5j`#GykpTNe}LRAS(qiyAY5v$0;>Hjs8%<ep++&)9ND+Z2NVn5QqO478x+j%d6OuZSaTtvz!$k1YTv+;K`oo2Ez9uSb<GfOoE=$nHq~><1HvKD)7`pFFFM2t{B`KsY+4k79j3h&Atq&~jVotvfWd|Y)fKrf2>rXqRB#D>XZ6)tV?3iQm#fb^z^Q)QjZIP3?p_lApEAhUKXNN9PtL2PxZgi+L^G>xN(C+R3P0gXPX%@<m^ljnSV^m1ELFK`DS>?*8K481l4gyI$V{f%vjTc?$>prGl#)KR4K`{3Q0*T88`|S8XDSG+{?%rMDp^@)knrsJ4JgXJ3@^Nw<P79_SYFXKGQ-rWS3oFx;<B5INCKx7gG^dVbX=bcb2~Z{h3cr9dC53xc=U|6zU2g3)9gop@4&K-GW7(M5U&EpS*Rl8Y&<O4I-YwQM2xnG-qGo(`<7Dum_3R*0#&|rS;CmuZ%^Xrw2V72=pWw(n+Op(E~#*@uqj1k;813{S@VLl<%ADikccrhu6-$Z9_y4Vp!2F4F4{5EEM1r7B3l`4nC-RwrEL$rBZ)%CViQ?+kPfQ-Q;*+fCat<gZ`u6Hjn+~VfcG9wW_z)U`UC${gPEx{QMXQ8+InE`>(w}4Rdq3O({jOAyW7SbFc51E$tcv6wrmwqEwML774$~2LE4hJgXGs@4O%f}s{m}HQ>EUv(yRB_>p;g$b)QA!S1S!`5uKD?6U3|<PvRH^=x>G0v-whUKrrrs=hX3srY@4@u%|YEQ=2-!{YY*j6H7w@ibu&==+El;9kyu4$l>>WL~80I>fo-==7@g#$Rp-kR<P{##w3Q}#z$;48}{xDDgoCPs~HKD;ad%oRcD~>1O9BNsS_Anny_@zkD1BDlGK(L(!`{C@i$0XIfRJ2BeaEc#12N;%q75F&%4n1e;lPAw41GJB8y;Hc7Wz!1Tx$4o#*^Wquz+8QQ^%sM)_@T299zx(&xGYKJ+$r^ln<}E*`g|1eMh1=Cb&jpiS-@(k0g_D58b`B2FE78v$e;M;8t3gNJIoj#<qN^;|Y?gidV;3Cls)@5u?^?QFbxcMoH4VT6U}gr@^QXmn9gP(u-031h)t8S(*)(3;p<J?q_XVlTy;o^c2KrLpbcWNNZ)bL9B#2r76)Vo6-ur<%J4@_qamWGVqmf9;NM22*{h6~MgTA;KLypDN1pokvEUG!!MT-{!uRahOIHN0e1Y0Dxga+^?6J3%k0U2MBIqGGm$|i$#K0rvW8>dbOLWGcA0NKU7ynVCge})o{)!=k7$#EyUB}T7A-fe3!NqtU)9Fble*#CM2>*SyaJCf{~(7r<Pd`{gBk$k0aSu{@{KnVr7b6pD%v>sGsaEim`JA#j-D6k@sQwE{9#DrI+zV$3GZ}1xI3thm>3)+5#X9V9iR#)REZEV001)QX+2<u<LTWys&(>OomJ7NU;qQ1vDLix7Qb(1H2*7Ay6V2IAj7PYKC{RV;^}0C1yEt)MG@TWPLVA1VENq>b3%J@@P$(r(2LmvfIkVhs5*p$gXF}VJl`qCx3gAInk^M;ys;3C*E72^VGbMZfj627fke`Hz4z0-qvIEg2}$X+neRAX=ZhezGOjzEepDaz?#`XLKnb2AsaOZJg`c&z1(e!>D~w6Fl+!#7}=|GE9tnRX<447A$0g-4B^oLmiYPm$mFJR6EKszc_2EDM%eMF3PPa%UefjW(+99(3=HG}OapWOSe&~n%M*(4U3^Bs;=3EM>+wi)V|GTvGw00m$kbRzTt!LZ%O{1?uoh%HF<Q5g026gt;XqrkY8;v{5KATWY7_FK8W>H+rFW95St`bIJb~e``ci&d#t6XkKbQ7G=eca{B2_u$r{$QUAuKH72$<p@`t);3iyXs~n3>@`P6eu+fuLXnHq02nNK+`5#?j=d4U5J_MoG1;S{Y2lT3))4h609N<4rA8IhP^(SBt%RFr}QPS?Q@)(twdVeo;N#!A#UVcHF3Py*N)pE-<A`akZCzW-qhZtE~2N>rts%0^`wJ*FuiJmBG@jL0bOYR2N3@)NQYs^)Cee^{nWq^Ps*3NXfl7&_g7Tbz37dji|2YIcpv*h;htBolXIOb2MyhMxv6+<TU@XC)_^#=9_;52|O}8',
    'body': 'c-pmCS+5jD6#g&s;>*O;-c|RFXiSWWF)j}(gwzT~R3d^R;lF#fs&4Px3m1i&N%!fl?W?n&esy~GG}rzxw-=`?ug<6Z=;7njl@90AqbDz)K7Mw(dUg8fboHZkXM1*Mb@u0z8k-tH^`M$RJvg7v&<}I5U!OG$aKpo2Wv8pc0Uyr+Mh5ud;g4M!y0lW~bk^93t1Ddxyi&@vMuh2MBf>hx1hoG^Sntya-m5gYX++=!fmR5C4;Z;WDwVp&W|YcRNh@ViwWii<0IK!meF4TOV`xmDW5Td%qA<EAn%7|EK{GrKsl6Ach*$Rzjv*`y4m91@GAg!~Cf#D}a!5Z6a7uuc1=tQ)+2IBDY}A=~L25XA>)t{09pE=PTyC(SXBvdLpQjas`3b_b0Mi~}ngl1QjKTLFL&&3Qlwj5T4z|wS@Jb0D`r<0Ikq!_2_|T5S(qx6t8kTOfob3qQ^`2l;+0H~{EW$y^pH9eT>Dq=2=rwAR4yZ;*y?c@rF}-#>X<%4hG@N0l<Isyv2fFNI44iCV)9iaW+zUZ4288(;!qihA7ffny8yo4P-?ve3qok=dSKW0k!ufpK?gYcO`{qAR{9-DyKAgj_7DU+uDJF>`k|`vGLf~C=W*a@UrkQjg{IU=`)Gb*zjJVDb!6@gEawlkCPE9yM6TR<o>my9EWwtJSt7!uw#WaWnOVN|0Axr`WKS@=Zo}}ri2?;~yTNpATLi_3_uAzdoY(+=?R>v;G*7nnlMb@c%I*vGXfSDb@(yjiNoZn6&w6AZrpQ*fz&BqSxm^1x>_iDER@JZ{vWqaUO?L=7Hj=+#Bkn!8t?GsGQ>^26vfH1$g$$=X1)4e52<J#t2Xr1=5Y})A%END!1>%kUqB5^)z7fWw;9|{6c&h8u&^`r>kU@wx_Hl1V3;^)7eX08{^I8Aj#i<}%0u9o?@;Cx^bp?!C09%(EW{r|}*oYo_X03gByGqR{I>QCML)+m~}+*tV$+V_{jbt6tc>{RTQgF#$Dqt^9Cdhu?>w_tx=!NvBzOST?j&O6Wu^M^~}f`Ly*tQ@)Ft*<<yw5fY(0SGhtsvWCtcb-z&*LxF|Rt1EXXS$;?!l?6x=HXDqX%*L#b%newB@2dB_ZXfx(Be*H?!g+3q^40s8gibI2DIvIN)>}K7*UHV^hW$Cd)5bm1@gvInT))FC_EXC+=5FW?m}7v2F6(lSRD_BRBI=u1ChZE{?%KI1~r4zX`9HZ0+vKjj_hbjQ%G?hwTMLPy3>;zRzd`MvZ>5d4;l%;%XE|zEof-Fc09Vmqu+jTAixL;9%@6MPyq{RfEiT;)2cwJJF&VHX_y@q<pC}aj}akZwVCtsen@@S;mO@OI&Zc%VTw|xA<6l{Robak#sV^G2Np07REoGt0VN>CBrWsI^}%UHIB+3%^q8<3%Fie^7zK%rGxFx{SKQ*!&S^IfhwL<Yva<?1{bFaoot==WQUc(JoiZJauV=Fg0$9xj3MdhC5bH3wQF;#!3^6?xOz}eTFYku5zSJ5}Ygvt3VZAPu$KCyoyZ;2cJB3x4Y+g$USS(!raQM$`8F#_T&Ij)fiU_!q&ni{7O#PKaQ$``53}+y(jpNZL)BM^r-EGgf`IGBdOTF!f!+$}>dag&{iqbA<<`rWCluIzqgEUga6uMBxN%2M)>PSI_TU0T<j|T+y>n`zyYf09>FUkIPlO?0QRZsez#RkQa+q6}(<RC6nd>K&Ei-DRgxmNauE_XLASrVD2M>C@Xf`1i<4JUjb4jUo>JM1?_iF!y?e+Ntf!|u*=*D`Q8LLuv<I;R=8UT~Rb7okBz9!a60G>;xYJfaEYIwT~t(GurXE;h+(keSv*DabWCMapq4W;YTV{$QWz_ng5}A<@|vW(}3I29HBA|CS46&lYP;GT`SIx>pN-9eB69=%yV-{AR&00*;h+d2yXfEJ>KfpFTjrG-WXOrGom<DR{6!%T?3{JygGdJ5G{|N@Chs{jji(B9uQ5Umj$`#`VEQNeiVdnfy*m9#hRurP=WC2af8FH6|!_QlY3CR6;LQRgNlVRVid?P!iuXfq>Z>#VmzfrJ5_Vu0}!@7}#Ie`QXU10<4m72`n-+K+TOa-c8P!=4X#83E|e!iDDH3RT2ge_KyV~EYHO4UasxjHMVmqkBJx;PF<7+zxyD|4fVqr_)KuEk;|Z&j+gma#?SO7%&$!J@d&CQ&Jlr=QYj&%zc1{CKQf`7L-W%Xs^qRwI4~1jJwNlzly+{fq2i(x!yUie-G7c>i4L9*8DS-%irvptc-A<Fn(kQIeehi8{&NEiL!1#n#xq(snD}X2G<(rb4_?3i2XDwu#{',
    'brief_head': 'c-p;IORv>75dJS&XAwUV+jm!>52Ut8K*a(O@)H&;kWi5j;=gwu9w#~H-rE)lA|0J?5_|l4JoAmeOdmhQT;Ig<X}Vd>JjJ(f-c2{k&C}cWpFh0&INf}iewuDxD&uBlXJzJPUgv4Sr?eIpd2DN~4lA})+u99P+XgSXwY8?VRux;RW&G~Q&<z2;!pFft8gBYx{CF^o7_ER6`Vg34m!<aU;59C5Ynw2t%k+Al9>``iZbso|5_zg6t+@EU4q)0@g{d8bn<m&4*prN};V?IEGDZWpRptV<binyAChY4L)p5;U5#@)s#$WqfYl$4>wf5N&i2-46v`rMONKrxR$?egRc<%>@LG^ciJI}+2^SVAkcy(Vd^72-=Bsyc|22b3~qdVf?hm1JDWWY*k3|~6Nf5a0g#u3jl;<+rjm0RMB8w`Ts-;#fYe{o+os^!QBDgTU=HBeR;DMM*;hKirTmzO%gezq6zU#Il}YG17$Akq8<X{v2j%Qek%Lc6c4we~oi(ET&+K}hUZBxe0Z{wkLsFVd!#W6l(P%BM^x&L!-#Q~x1<6`w`_)-9M<7D*J3`Md2_U(alrJPa<?FFQ}Cc{9J=n!h4}+c#i&F0sYOeVfmLk@91p4BBo_g#Ygk9sMpDrmpsWm9XCn9xA0jM@TgPK$@%Mo6zKrW29v1{5@Nhn^OS*R;)Nwx01<9D0QxdLY6~`%gwT-q4e;_7QA0K`0JKKwOPe7t<<`Rh3zcvmM1+G%Me$va5I12ns2dd8|92S;5=||z=UI<^k)o>(F+EWRSSkC<G_$SMliPIB3M_>&)6Hmz~Gnj?a4j$-uu<4v8?ubPegyzCKdjuTd3!BsCRgO=vNtbar$<e7f(Jd60L#POWeoL{fc<nE?!S1{^n9uYj#J$MDAc{Xj$laTme|64u&7YGP2nnxZPVdBk>(`?+!BMhTKdj5yUk$Wieong>Mhfq<iVZX(+rrRBYaKp0)DT0WL{!K00GgWsac1YY~LaE0I|opTkPFj&)Z`__m?#hCYK@n^-n!${6?!Hty(Zc9Q%+d>m7LE;_SQzDp-j3-JDjlF%z!%kn=8BjvxY%d`iOj{N)JDl+fnk{7UTKu9-j0$q-S1Q`>`M$jPaqD1)xQg&fhenh#u551N^7X$CH@J$;p=qqWJ0<CO{uIH8oWkroxadO4O&KRE%(NV@S^Za^s<HC;$14u(1E6XYd?=3D=8#KPkiqDdpn(H#-T8UT@9)y~!8XQ!dZjqDj5<t^YlFDcuiPMnwh5>l>w_cRRC<M4Ng;_%o;QXd`{gmrxdj0k5KiSK%KL',
    'brief': 'c-pmC$&MUF5dD|FaA{EPmE{}DnFHd65X#j?7_cxHS%`n<#gbKpX9gK$YFgFNRhbztUMv|of81WbDs6mM`kULcXzsW2{JR&oXExn$&tJZM_2TvI*&nx$ZqL5);qLF@Ztn4ZGjlUDnUPG7w{P#aJKke1y|;IZ0bxdbObNCb8t^d&By&%9hXt&=-~7boY{F$}z$a@3rz^x6@u61+udKl|o+<i`uVYkiAdDJg9T02BPt&V0Ba@Ve@xXv9P9J6<316plzCCA{BCC{RWoJ%p1jj0zozPf8W81Ve&GpWL8);*~2O|Qm{~-7n_nBfe`;?2ha*q?zftL(p*zk^NVoJj^VoC|ZWyM^=-9?{kO@uIt2yu<^W7BD^N4|`mS2+GLIDr_8%x+OQ<QawIc)6+|@=!m_=H*G;+6b!E)M0FLLW;AakW_{>nN}`yr>W4^lK3Y)21j^NeSJx#)vCrik>EHZQiUFtHlm0m&yYyU%l^%Ix?1z<HeF98f|DMFlRM)jpQMn9oixez7_MuKoZ9F_|Liq{eP)uxe!OKS(sars*fAT2D;R^7J%JrkVs~hZ0_RhL;~2}89XqC9T66FFl6%fWO^eeJJ7&4AGzkw%C(Wsyv9%%#@<p?^5d*GBfz%iE9ScU0Q7H(qYODnFvjx*0S+?<VeRpIjaw6u@#b~xYERl#5F_5xNa8OiZ8c?Lx*8q;jC4$o9X;&3n1A(fz1Yz)Vg609uUm0|J8|qR-6C9Vyq?B?)5-XCo%8>QVjvu3$^P2nR$GHCJ*J1neQiMHjbSDW~IlRXXrK-+lz^Md>Ab+tSyT7psz}Xt5Gwp-YP${r&oFq}sE%{0l^1vSQev#`r#=)|4O?T=F>KesBFuz<duTHNk6}B<c5_^%Tq^DXDNYs#G5fNsW$U{U#c*G?l`Ro$i*t?1tvYukd%mnSL#~EDkC0ZyV?O}Pu9(gcwvVep+o_k?LE~<STp+V}ljBy+cN0gr)GL`2l%LoC2`8C0`i$RXfqgKuA3F6GSdjWWq*#B81Xl2zwOQq1<w_}&^Qk{1nWV7We;^y{Fa$rjsgT*qEca}uUqgZqt9hnF87W}^RmWG|XXOmDW2t+;iZe%aIm0Mlu^@vbqGQtE!nu>4b^h0z@xdQt#7$xTvmh*IQ$EQV~fwUE`<(#lIVA&bUm5#n!-h@M>#BYtM33jpJH3v9~Bsph3wr4H|QKwV*^Ma1m^{eTIOn=(&M!OyyQ>i*4Y#Oj|;dZmBV|r64?G%nzhAWbvjr<W(Co^cr^F_MBaoH0O<GIHQ(t>!uQ-NUf>8|#pDe^0tod+_$E);0XvuED!5d>ThRxd)Tr}UZW!a^B?_Mq%#GliFN8B{ZBQ~1gI-$}*ulj*RGBRXAKbT*|k9(0bU>BK(46)rHHI^Cdx7I$<CSS=)N>=MQVDl7)g1E^$7FBDUL5cm(j9Y=j_Em71;822i1U7L)1|8LU%J+ucyt-UI5HBo<BAO6wsA0#v02dflx`VQzW@a?H>t<6#cPd2b?>a4tt!iF%j%*)u|cs^QS{`RAg@|W*ot?j8l8vY{@8>Jh-oxEKs&0By5^idcW;f+0qjkt8&5TAqw4p3!_Td5E6gMj^Xdi=n3cs710&;I;aCR4sO?fo?eHIw_wRnFw3B~xn|Bz=p%LNmEFsfM9&^BuHCkm^_0G-Cr%U$tPv!Vgifu>(lK{-<4H354kvIp)R-=b;xcoYCP1Y0PEDlQ&xC^@FW}T6o?XYL8R_v?991r9-!bKKm|PZ^)gaOvv;uYo~6hC~|+{OFy=TU!^9-v!C_cDGjNG#iDPus5n$vpSq!Q@zmjQ0{`|P_T+>@S@UncH8%aMS~n|gBPgV-<;}Y+>G`%-IZGkH<e*DO7=A}Z0mm5qw*U%89&!vca^gX|qP@##eYLe&o$~vo?^lIgdb5q27H(S#*PXscI=&C?J!ixRj9QfB2qbMcsTv#=cB(?nlx%V_jkhd|Ac@^F2+X$RX6;lPpG%6wYG!15;C*}W5Z>WI+Ar#iq>CKtMLMAo2aexkQBi_>%hK>~deErrloD6Jk=A*Tk9o#w(+1O8&^-9_&%Xebkc%k',
    'footer': 'c-oa!$!-)e5dD|FaOs2Bc6)A!8z;mG38Khb6C{?101}}5JMWd<lgT7e#H45Jj;mf(y;}Tty17oJU8eeLI@mZ*>Eq?qbkKI5K7RgveRVS({!TBZ!+R5EGuv6=JK1KdDbvL~9dH6IGlyBv3$&v;eo~~wOGrdJYsE*jab&k$E~Yki&6GtpOHoUf9sZ%4p?uT8TPeTsQz`E#QoZt3gx93<DmzHi@+(-@O5ZnaVr_L5p=h)#MX8*qq>I&?9lqF2KiKKb?UCi~UUtf~WVOveIU>{aYnToSgq#@OHi^_f^SgqXrTXSfSyiYl3gDa0;wr%quz-aI2TFivOS7H367H=FIHg?aa)Z)GR~mUc2#fcv)KzzNThfqs?QCO8R21IYszlf^Z*mm#*ytLDmT!jk-u0m3ktN-{$Ssgy!c$lGRdP^6^&=;#I~{62vCZ_tt1KAbZBork^#F+G5|grm!!R>7ld`$iC~P77gCA583b2%xh|2mzC|daf!~`l(HpD7D!QqHyazl9V5$=1}YkCysc;gvMoRXtVYWFCdwg%M7+2Tsgp{R!7N)fbB1bf-vG|o(=WXquvx}67WQV*84L6#`m2BPJo?cRorB7g+SCnIidy~*93o32)Zs2o5_D_kG@Qu*pZjHAoW7GGMiYD-$Btk`OZkY`UUg#JXoSf_W;Mwt$09zIn0{Futq4^_UfD>VGqM=t4XLLLib5-JXBj^Y?65ZHsVa1iqITiW=#lXSG;{*Mkp`Su{^C~zQ1PSFxQ=bM(=(VH3X{hZB4`KSf!ddCu?0HzsqhTHThqBiLirz1nrWXo~LX)@B!7nH4$RO~4^U1{VyjJPoS6JpW98%8R2du^QkQ19lv`!FY=$Xmh`qgxOYHrCp^+El+3Ot#|HdN-th>}4H+;(!tn0Y)X-Jj(5I`sL_Zo6M1)XUSslXvL?O-n#~Ojjt`?dLzp3J%*iNxx7M_<iHvpTctoE4sZ?1D2pZc2`G1wt^MZWPz`O}Y5j9Xk70*zV-m`cD`N`F3~*!Sa-eJ!b%OHYCrh+v$ly<-7$&!wFkRf<{sTh@`GE',
}

STYLES = {}


def _load_styles():
    for name, blob in GLYPH_BLOBS.items():
        raw = zlib.decompress(base64.b85decode(blob.encode()))
        data = json.loads(raw.decode())
        glyphs = {}
        for ch, (adv, w, h, dx, dy, hexdata) in data["glyphs"].items():
            glyphs[ch] = (adv, w, h, dx, dy, bytes.fromhex(hexdata))
        STYLES[name] = (data["space_adv"], data["ag_h"], glyphs)


# --------------------------------------------------------------------------
# The day's news — Monday, 23 November 2026 (frozen data)
# --------------------------------------------------------------------------
LEAD = {
    "kicker": "US POLITICS  ·  WASHINGTON  ·  TOP STORY",
    "headline": "Democrats Clinch Historic House Majority",
    "body": (
        "Democrats have clinched at least 258 seats in the US House of "
        "Representatives, the Associated Press reported — the largest "
        "majority won by either party since 1992. Republicans keep control "
        "until the new Congress is sworn in on January 3."
    ),
    "chips": ["At least 258 House seats", "Biggest majority since 1992", "New Congress sits Jan 3"],
}

STORIES = [
    {
        "kicker": "RUSSIA–UKRAINE WAR",
        "headline": "Russian Strikes Kill at Least 15 Across Ukraine",
        "body": (
            "Rescuers dug for survivors under a collapsed block of flats in "
            "Dymer, near Kyiv, after Russian strikes killed at least 15 — "
            "days after Putin promised a 'painful' response."
        ),
    },
    {
        "kicker": "ESPIONAGE  ·  COPENHAGEN",
        "headline": "Denmark Accuses Russia of Plot to Kill Rapper",
        "body": (
            "Danish authorities say they stopped three men linked to a banned "
            "street gang before a planned hit on musician Kyivstoner, and are "
            "expelling Russia's defence attaché."
        ),
    },
    {
        "kicker": "MIDDLE EAST  ·  IRAN",
        "headline": "Trump Warns of Renewed Iran Strikes by New Year",
        "body": (
            "President Trump said he is inclined to resume military conflict "
            "with Iran if no deal is reached by the New Year. Tehran vowed "
            "to fight the US naval blockade."
        ),
    },
    {
        "kicker": "SPORT  ·  TENNIS",
        "headline": "Alcaraz Beats Zverev to Win First ATP Finals Title",
        "body": (
            "Carlos Alcaraz beat Alexander Zverev in straight sets to claim "
            "his first ATP Finals championship, capping a remarkable year "
            "with a third straight tournament victory."
        ),
    },
]

BRIEFS = [
    ("INDONESIA", "Death toll in the Banten candy-factory fire reaches 24, with about 30 workers still missing."),
    ("BELGIUM", "Airports face a nationwide shutdown as unions strike against austerity cuts."),
    ("ATLANTA", "Delta says the systems outage that delayed more than 1,600 flights has been resolved."),
    ("TECH", "Reports link the woman in Nvidia's scandal to a Chinese state-security official."),
    ("US", "Trump signs the Common Cents Act, ending the penny's 232-year run."),
]

FOOTER = "Compiled from the day's reports: Associated Press · Reuters · Al Jazeera · Xinhua"

# --------------------------------------------------------------------------
# Canvas drawing
# --------------------------------------------------------------------------
canvas = bytearray(bytes(PAPER) * (W * H))


def rect(x0, y0, x1, y1, color):
    """Filled rectangle, inclusive bounds, clipped to the canvas."""
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W - 1, x1)
    y1 = min(H - 1, y1)
    if x1 < x0 or y1 < y0:
        return
    row = bytes(color) * (x1 - x0 + 1)
    for yy in range(y0, y1 + 1):
        off = (yy * W + x0) * 3
        canvas[off:off + len(row)] = row


def rounded_rect(x0, y0, x1, y1, radius, color):
    """Filled rectangle with rounded corners, inclusive bounds."""
    height = y1 - y0 + 1
    for t in range(height):
        d = min(t, height - 1 - t)
        if d < radius:
            inset = radius - int((radius * radius - (radius - d) ** 2) ** 0.5 + 0.5)
        else:
            inset = 0
        rect(x0 + inset, y0 + t, x1 - inset, y0 + t, color)


def hline(x0, x1, y, color, width=1):
    rect(x0, y, x1, y + width - 1, color)


def vline(x, y0, y1, color, width=1):
    rect(x, y0, x + width - 1, y1, color)


def blit(px, py, w, h, packed, color):
    """Blend one glyph's 4-bit coverage bitmap onto the canvas."""
    fr, fg, fb = color
    idx = 0
    for yy in range(h):
        cy = py + yy
        if cy < 0 or cy >= H:
            idx += w
            continue
        base = cy * W * 3
        for xx in range(w):
            byte = packed[idx >> 1]
            cov = (byte >> 4) if (idx & 1) == 0 else (byte & 15)
            idx += 1
            if cov:
                cx = px + xx
                if 0 <= cx < W:
                    off = base + cx * 3
                    if cov == 15:
                        canvas[off] = fr
                        canvas[off + 1] = fg
                        canvas[off + 2] = fb
                    else:
                        inv = 15 - cov
                        canvas[off] = (fr * cov + canvas[off] * inv) // 15
                        canvas[off + 1] = (fg * cov + canvas[off + 1] * inv) // 15
                        canvas[off + 2] = (fb * cov + canvas[off + 2] * inv) // 15


def measure(text, style):
    """Text width in tenths of a pixel, from the glyph advances."""
    space_adv, _ag_h, glyphs = STYLES[style]
    total = 0
    for ch in text:
        if ch == " ":
            total += space_adv
        else:
            g = glyphs.get(ch)
            total += g[0] if g else space_adv
    return total


def text(x, y, s, style, color):
    """Draw a string with its ascender line at y; returns end x (pixels)."""
    space_adv, _ag_h, glyphs = STYLES[style]
    pen = x * 10
    for ch in s:
        if ch == " ":
            pen += space_adv
            continue
        g = glyphs.get(ch)
        if g is None:
            pen += space_adv
            continue
        adv, w, h, dx, dy, packed = g
        if w:
            blit((pen + 5) // 10 + dx, y + dy, w, h, packed, color)
        pen += adv
    return (pen + 5) // 10


def wrap(s, style, max_width_px):
    """Greedy word wrap; returns lines fitting max_width_px."""
    limit = max_width_px * 10
    lines, current = [], ""
    for word in s.split():
        trial = word if not current else current + " " + word
        if measure(trial, style) <= limit:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text_block(x, y, s, style, color, max_width, line_gap=6):
    """Draw wrapped text; returns the y just below the block."""
    _space_adv, ag_h, _glyphs = STYLES[style]
    line_h = ag_h + line_gap
    for line in wrap(s, style, max_width):
        text(x, y, line, style, color)
        y += line_h
    return y


def centered(y, s, style, color):
    w = measure(s, style)
    text((W * 10 - w) // 20, y, s, style, color)
    return y + STYLES[style][1]


# --------------------------------------------------------------------------
# Compose the front page
# --------------------------------------------------------------------------


def build():
    # Outer frame
    rect(14, 14, W - 15, 15, LIGHT_RULE)
    rect(14, H - 16, W - 15, H - 15, LIGHT_RULE)
    rect(14, 14, 15, H - 15, LIGHT_RULE)
    rect(W - 16, 14, W - 15, H - 15, LIGHT_RULE)

    x0, x1 = MARGIN, W - MARGIN
    y = 40

    # Masthead
    y = centered(y, "O N E - P A G E   W O R L D   B R I E F I N G", "top_kicker", ACCENT) + 10
    y = centered(y, "THE WORLD TODAY", "masthead", INK) + 8
    y = centered(y, "Monday, November 23, 2026  ·  The day's biggest stories, summed up in a single image",
                 "date_line", MUTED) + 14
    hline(x0, x1, y, RULE, 3)
    hline(x0, x1, y + 4, RULE, 1)
    y += 22

    # Lead story
    text(x0, y, LEAD["kicker"], "kicker", ACCENT)
    y += 26
    y = text_block(x0, y, LEAD["headline"], "lead_head", INK, CONTENT_W, line_gap=8) + 6
    y = text_block(x0, y, LEAD["body"], "lead_body", BODY_INK, CONTENT_W, line_gap=9) + 14

    # Lead stat chips
    cx = x0
    for chip in LEAD["chips"]:
        tw = (measure(chip, "chip") + 5) // 10
        rounded_rect(cx, y, cx + tw + 28, y + 34, 8, CHIP_BG)
        text(cx + 14, y + 7, chip, "chip", CHIP_INK)
        cx += tw + 44
    y += 48

    hline(x0, x1, y, LIGHT_RULE, 2)
    y += 20

    # 2 x 2 story grid
    col_gap = 36
    col_w = (CONTENT_W - col_gap) // 2
    grid_top = y
    for row in range(2):
        col_x = [x0, x0 + col_w + col_gap]
        max_bottom = grid_top
        for col in range(2):
            s = STORIES[row * 2 + col]
            sy = grid_top
            text(col_x[col], sy, s["kicker"], "kicker", ACCENT)
            sy += 25
            sy = text_block(col_x[col], sy, s["headline"], "head", INK, col_w, line_gap=5) + 4
            sy = text_block(col_x[col], sy, s["body"], "body", BODY_INK, col_w, line_gap=6)
            max_bottom = max(max_bottom, sy)
        # vertical divider between the two columns
        vline(x0 + col_w + col_gap // 2, grid_top + 2, max_bottom - 4, LIGHT_RULE, 1)
        grid_top = max_bottom + 20
        if row == 0:
            hline(x0, x1, grid_top - 10, LIGHT_RULE, 1)
    y = grid_top + 4

    hline(x0, x1, y, RULE, 2)
    y += 12

    # In brief
    text(x0, y, "AROUND THE WORLD — IN BRIEF", "brief_head", INK)
    y += 32
    for place, line in BRIEFS:
        label = place + "  —  "
        lw = (measure(label, "brief_head") + 5) // 10
        text(x0, y, label, "brief_head", ACCENT)
        y = text_block(x0 + lw, y, line, "brief", BODY_INK, CONTENT_W - lw, line_gap=5) + 5

    # Footer pinned near the foot of the page
    y = max(y + 8, H - 92)
    hline(x0, x1, y, RULE, 1)
    y += 12
    centered(y, FOOTER, "footer", MUTED)


# --------------------------------------------------------------------------
# PNG encoding (zlib, filter 0) and entry point
# --------------------------------------------------------------------------


def encode_png():
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    stride = W * 3
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += canvas[yy * stride:(yy + 1) * stride]
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))


def main():
    _load_styles()
    build()
    out = os.environ.get("ENTRY_OUT")
    if not out:
        base = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
        out = os.path.join(base, "entry.png")
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out, "wb") as f:
        f.write(encode_png())


if __name__ == "__main__":
    main()
