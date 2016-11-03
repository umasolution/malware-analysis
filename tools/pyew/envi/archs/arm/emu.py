
"""
The initial arm module.
"""

import struct

import envi
from envi.archs.arm import ArmModule
from envi.archs.arm.regs import *
from envi.archs.arm.thumbdisasm import *    #this gets both arm and thumb



# CPU state (memory, regs inc SPSRs and banked registers)
# CPU mode  (User, FIQ, IRQ, supervisor, Abort, Undefined, System)
# 
# instruction code
# exception handler code
# FIXME: SPSR handling is not certain.  

# calling conventions
class ArmArchitectureProcedureCall(envi.CallingConvention):
    """
    Implement calling conventions for your arch.
    """
    def setReturnValue(self, emu, value, ccinfo=None):
        esp = emu.getRegister(REG_ESP)
        eip = struct.unpack("<L", emu.readMemory(esp, 4))[0]
        esp += 4 # For the saved eip
        esp += (4 * argc) # Cleanup saved args

        emu.setRegister(REG_ESP, esp)
        emu.setRegister(REG_EAX, value)
        emu.setProgramCounter(eip)


    def getCallArgs(self, emu, count):
        return emu.getRegisters(0xf)  # r0-r3 are used to hand in parameters.  additional parms are stored and pointed to by r0

aapcs = ArmArchitectureProcedureCall()

class CoProcEmulator:       # useful for prototyping, but should be subclassed
    def __init__(self):
        pass

    def stc(self, parms):
        print >>sys.stderr,"CoProcEmu: stc(%s)"%repr(parms)
    def ldc(self, parms):
        print >>sys.stderr,"CoProcEmu: ldc(%s)"%repr(parms)
    def cdp(self, parms):
        print >>sys.stderr,"CoProcEmu: cdp(%s)"%repr(parms)
    def mcr(self, parms):
        print >>sys.stderr,"CoProcEmu: mcr(%s)"%repr(parms)
    def mcrr(self, parms):
        print >>sys.stderr,"CoProcEmu: mcrr(%s)"%repr(parms)
    def mrc(self, parms):
        print >>sys.stderr,"CoProcEmu: mrc(%s)"%repr(parms)
    def mrrc(self, parms):
        print >>sys.stderr,"CoProcEmu: mrrc(%s)"%repr(parms)



class ArmEmulator(ArmModule, ArmRegisterContext, envi.Emulator):

    def __init__(self):
        ArmModule.__init__(self)

        self.coprocs = [CoProcEmulator() for x in xrange(16)]       # FIXME: this should be None's, and added in for each real coproc... but this will work for now.

        seglist = [ (0,0xffffffff) for x in xrange(6) ]
        envi.Emulator.__init__(self, segs=seglist)

        ArmRegisterContext.__init__(self)

        self.addCallingConvention("Arm Arch Procedure Call", aapcs)

    def undefFlags(self):
        """
        Used in PDE.
        A flag setting operation has resulted in un-defined value.  Set
        the flags to un-defined as well.
        """
        self.setRegister(REG_EFLAGS, None)

    def setFlag(self, which, state, mode=PM_usr):   # FIXME: CPSR?
        flags = self.getSPSR(mode)
        if state:
            flags |= which
        else:
            flags &= ~which
        self.setSPSR(mode, flags)

    def getFlag(self, which, mode=PM_usr):          # FIXME: CPSR?
        #if (flags_reg == None):
        #    flags_reg = proc_modes[self.getProcMode()][5]
        #flags = self.getRegister(flags_reg)
        flags = self.getSPSR(mode)
        if flags == None:
            raise envi.PDEUndefinedFlag(self)
        return bool(flags & which)

    def readMemValue(self, addr, size):
        bytes = self.readMemory(addr, size)
        if bytes == None:
            return None
        #FIXME change this (and all uses of it) to passing in format...
        #FIXME: Remove byte check and possibly half-word check.  (possibly all but word?)
        if len(bytes) != size:
            raise Exception("Read Gave Wrong Length At 0x%.8x (va: 0x%.8x wanted %d got %d)" % (self.getProgramCounter(),addr, size, len(bytes)))
        if size == 1:
            return struct.unpack("B", bytes)[0]
        elif size == 2:
            return struct.unpack("<H", bytes)[0]
        elif size == 4:
            return struct.unpack("<L", bytes)[0]
        elif size == 8:
            return struct.unpack("<Q", bytes)[0]

    def writeMemValue(self, addr, value, size):
        #FIXME change this (and all uses of it) to passing in format...
        #FIXME: Remove byte check and possibly half-word check.  (possibly all but word?)
        if size == 1:
            bytes = struct.pack("B",value & 0xff)
        elif size == 2:
            bytes = struct.pack("<H",value & 0xffff)
        elif size == 4:
            bytes = struct.pack("<L", value & 0xffffffff)
        elif size == 8:
            bytes = struct.pack("<Q", value & 0xffffffffffffffff)
        self.writeMemory(addr, bytes)

    def readMemSignedValue(self, addr, size):
        #FIXME: Remove byte check and possibly half-word check.  (possibly all but word?)
        bytes = self.readMemory(addr, size)
        if bytes == None:
            return None
        if size == 1:
            return struct.unpack("b", bytes)[0]
        elif size == 2:
            return struct.unpack("<h", bytes)[0]
        elif size == 4:
            return struct.unpack("<l", bytes)[0]

    def executeOpcode(self, op):
        # NOTE: If an opcode method returns
        #       other than None, that is the new eip
        x = None
        if op.prefixes >= 0xe or op.prefixes == (self.getRegister(REG_FLAGS)>>28):         #nearly every opcode is optional
            meth = self.op_methods.get(op.mnem, None)
            if meth == None:
                raise envi.UnsupportedInstruction(self, op)
            x = meth(op)
            print >>sys.stderr,"executed instruction, returned: %s"%x

        if x == None:
            pc = self.getProgramCounter()
            x = pc+op.size

        self.setProgramCounter(x)

    def doPush(self, val):
        esp = self.getRegister(REG_ESP)
        esp -= 4
        self.writeMemValue(esp, val, 4)
        self.setRegister(REG_ESP, esp)

    def doPop(self):
        esp = self.getRegister(REG_ESP)
        val = self.readMemValue(esp, 4)
        self.setRegister(REG_ESP, esp+4)
        return val

    def getProcMode(self):
        return self._rctx_vals[REG_CPSR] & 0x1f     # obfuscated for speed.  could call getCPSR but it's not as fast

    def getCPSR(self):
        return self._rctx_vals[REG_CPSR]

    def setCPSR(self, psr):
        self._rctx_vals[REG_CPSR] = psr

    def getSPSR(self, mode):
        return self._rctx_vals[((mode&0xf)*17)+16]

    def setSPSR(self, mode, psr):
        self._rctx_vals[((mode&0xf)*17)+16] = psr

    def setProcMode(self, mode):
        # write current psr to the saved psr register for current mode
        curSPSRidx = proc_modes[self.getProcMode()][5]
        self._rctx_vals[curSPSRidx] = self._rctx_vals[REG_CPSR]

        # do we restore saved spsr?
        cpsr = self._rctx_vals[REG_CPSR] & 0xffffffe0
        self._rctx_vals[REG_CPSR] = cpsr | mode

    def getRegister(self, index, mode=None):
        """
        Return the current value of the specified register index.
        """
        if mode == None:
            mode = self.getProcMode() & 0xf
        else:
            mode &= 0xf
        idx = (index & 0xffff)
        ridx = idx + (mode*17)                # account for different banks of registers
        ridx = reg_table[ridx][2]         # magic pointers allowing overlapping banks of registers
        if idx == index:
            return self._rctx_vals[ridx]

        offset = (index >> 24) & 0xff
        width  = (index >> 16) & 0xff

        mask = (2**width)-1
        return (self._rctx_vals[ridx] >> offset) & mask

    def setRegister(self, index, value, mode=None):
        """
        Set a register value by index.
        """
        if mode == None:
            mode = self.getProcMode() & 0xf
        else:
            mode &= 0xf

        self._rctx_dirty = True

        idx = (index & 0xffff)
        ridx = idx + (mode*17)            # account for different banks of registers
        ridx = reg_table[ridx][2]         # magic pointers allowing overlapping banks of registers
        if idx == index:
            self._rctx_vals[ridx] = (value & self._rctx_masks[ridx])      # FIXME: hack.  should look up index in proc_modes dict?
            return

        # If we get here, it's a meta register index.
        # NOTE: offset/width are in bits...
        offset = (index >> 24) & 0xff
        width  = (index >> 16) & 0xff

        #FIXME is it faster to generate or look thses up?
        mask = (2**width)-1
        mask = mask << offset

        # NOTE: basewidth is in *bits*
        basewidth = self._rctx_widths[ridx]
        basemask  = (2**basewidth)-1

        # cut a whole in basemask at the size/offset of mask
        finalmask = basemask ^ mask

        curval = self._rctx_vals[ridx]

        self._rctx_vals[ridx] = (curval & finalmask) | (value << offset)

    def integerSubtraction(self, op):
        """
        Do the core of integer subtraction but only *return* the
        resulting value rather than assigning it.
        (allows cmp and sub to use the same code)
        """
        # Src op gets sign extended to dst
        #FIXME account for same operand with zero result for PDE
        src1 = self.getOperValue(op, 1)
        src2 = self.getOperValue(op, 2)
        Sflag = op.iflags & IF_PSR_S

        if src1 == None or src2 == None:
            self.undefFlags()
            return None

        return self.intSubBase(src1, src2, Sflag)

    def intSubBase(self, src1, src2, Sflag=0, rd=0):
        # So we can either do a BUNCH of crazyness with xor and shifting to
        # get the necissary flags here, *or* we can just do both a signed and
        # unsigned sub and use the results.


        usrc = e_bits.unsigned(src1, 4)
        udst = e_bits.unsigned(src2, 4)

        ssrc = e_bits.signed(src1, 4)
        sdst = e_bits.signed(src2, 4)

        ures = udst - usrc
        sres = sdst - ssrc

        if Sflag:
            curmode = self.getProcMode() 
            if rd == 15:
                if(curmode != PM_sys and curmode != PM_usr):
                    self.setCPSR(self.getSPSR(curmode))
                else:
                    raise Exception("Messed up opcode...  adding to r15 from PM_usr or PM_sys")
            self.setFlag(PSR_C, e_bits.is_unsigned_carry(ures, 4))
            self.setFlag(PSR_Z, not ures)
            self.setFlag(PSR_N, e_bits.is_signed(ures, 4))
            self.setFlag(PSR_V, e_bits.is_signed_overflow(sres, 4))

        #print "s2size/s1size: %d %d" % (s2size, s1size)
        #print "unsigned: %d %d %d" % (usrc, udst, ures)
        #print "signed: %d %d %d" % (ssrc, sdst, sres)
        
        #if Sflag:
        #    self.setFlag(PSR_N, sres>>32)
        #    self.setFlag(PSR_Z, sres==0)
        #    self.setFlag(PSR_C, e_bits.is_unsigned_carry(ures, s2size))
        #    self.setFlag(PSR_V, e_bits.is_signed_overflow(sres, s2size))

        return ures


    def logicalAnd(self, op):
        src1 = self.getOperValue(op, 1)
        src2 = self.getOperValue(op, 2)

        # PDE
        if src1 == None or src2 == None:
            self.undefFlags()
            self.setOperValue(op, 0, None)
            return

        res = src1 & src2

        self.setFlag(PSR_N, 0)
        self.setFlag(PSR_V, 0)
        self.setFlag(PSR_C, 0)
        self.setFlag(PSR_Z, not res)
        return res

    def i_and(self, op):
        res = self.logicalAnd(op)
        self.setOperValue(op, 0, res)
        
    def i_stm(self, op):
        srcreg = self.getOperValue(op,0)
        regmask = self.getOperValue(op,1)
        pc = self.getRegister(REG_PC)       # store for later check

        start_address = self.getRegister(srcreg)
        addr = start_address
        for reg in xrange(16):
            if reg in regmask:
                val = self.getRegister(reg)
                if op.iflags & IF_DAIB_B:
                    if op.iflags & IF_DAIB_I:
                        addr += 4
                    else:
                        addr -= 4
                    self.writeMemValue(addr, val, 4)
                else:
                    self.writeMemValue(addr, val, 4)
                    if op.iflags & IF_DAIB_I:
                        addr += 4
                    else:
                        addr -= 4
                if op.opers[0].oflags & OF_W:
                    self.setRegister(srcreg,addr)
        #FIXME: add "shared memory" functionality?  prolly just in strex which will be handled in i_strex
        # is the following necessary?  
        newpc = self.getRegister(REG_PC)    # check whether pc has changed
        if pc != newpc:
            return newpc

    i_stmia = i_stm


    def i_ldm(self, op):
        srcreg = self.getOperValue(op,0)
        regmask = self.getOperValue(op,1)
        pc = self.getRegister(REG_PC)       # store for later check

        start_address = self.getRegister(srcreg)
        addr = start_address
        for reg in xrange(16):
            if reg in regmask:
                if op.iflags & IF_DAIB_B:
                    if op.iflags & IF_DAIB_I:
                        addr += 4
                    else:
                        addr -= 4
                    regval = self.readMemValue(addr, 4)
                    self.setRegister(reg, regval)
                else:
                    regval = self.readMemValue(addr, 4)
                    self.setRegister(reg, regval)
                    if op.iflags & IF_DAIB_I:
                        addr += 4
                    else:
                        addr -= 4
                if op.opers[0].oflags & OF_W:
                    self.setRegister(srcreg,addr)
        #FIXME: add "shared memory" functionality?  prolly just in ldrex which will be handled in i_ldrex
        # is the following necessary?  
        newpc = self.getRegister(REG_PC)    # check whether pc has changed
        if pc != newpc:
            return newpc

    i_ldmia = i_ldm

    def i_ldr(self, op):
        # hint: covers ldr, ldrb, ldrbt, ldrd, ldrh, ldrsh, ldrsb, ldrt   (any instr where the syntax is ldr{condition}stuff)
        val = self.getOperValue(op, 1)
        self.setOperValue(op, 0, val)
        if op.opers[0].reg == REG_PC:
            return val





    def i_add(self, op):
        src1 = self.getOperValue(op, 1)
        src2 = self.getOperValue(op, 2)
        
        #FIXME PDE and flags
        if src1 == None or src2 == None:
            self.undefFlags()
            self.setOperValue(op, 0, None)
            return

        dsize = op.opers[0].tsize
        ssize = op.opers[1].tsize
        s2size = op.opers[2].tsize

        usrc1 = e_bits.unsigned(src1, 4)
        usrc2 = e_bits.unsigned(src2, 4)
        ssrc1 = e_bits.signed(src1, 4)
        ssrc2 = e_bits.signed(src2, 4)

        ures = usrc1 + usrc2
        sres = ssrc1 + ssrc2


        self.setOperValue(op, 0, ures)

        curmode = self.getProcMode() 
        if op.flags & IF_S:
            if op.opers[0].reg == 15 and (curmode != PM_sys and curmode != PM_usr):
                self.setCPSR(self.getSPSR(curmode))
            else:
                raise Exception("Messed up opcode...  adding to r15 from PM_usr or PM_sys")
            self.setFlag(PSR_C, e_bits.is_unsigned_carry(ures, dsize))
            self.setFlag(PSR_Z, not ures)
            self.setFlag(PSR_N, e_bits.is_signed(ures, dsize))
            self.setFlag(PSR_V, e_bits.is_signed_overflow(sres, dsize))

    def i_b(self, op):
        return self.getOperValue(op, 0)

    def i_bl(self, op):
        self.setRegister(REG_LR, self.getRegister(REG_PC))
        return self.getOperValue(op, 0)

    def i_tst(self, op):
        src1 = self.getOperValue(op, 0)
        src2 = self.getOperValue(op, 1)

        dsize = op.opers[0].tsize
        ures = src1 & src2

        self.setFlag(PSR_N, e_bits.is_signed(ures, dsize))
        self.setFlag(PSR_Z, (0,1)[ures==0])
        self.setFlag(PSR_C, e_bits.is_unsigned_carry(ures, dsize))
        #self.setFlag(PSR_V, e_bits.is_signed_overflow(sres, dsize))
        
    def i_rsb(self, op):
        src1 = self.getOperValue(op, 1)
        src2 = self.getOperValue(op, 2)
        
        #FIXME PDE and flags
        if src1 == None or src2 == None:
            self.undefFlags()
            self.setOperValue(op, 0, None)
            return

        dsize = op.opers[0].tsize
        ssize = op.opers[1].tsize
        s2size = op.opers[2].tsize

        usrc1 = e_bits.unsigned(src1, 4)
        usrc2 = e_bits.unsigned(src2, 4)
        ssrc1 = e_bits.signed(src1, 4)
        ssrc2 = e_bits.signed(src2, 4)

        ures = usrc2 - usrc1
        sres = ssrc2 - ssrc1


        self.setOperValue(op, 0, ures)

        curmode = self.getProcMode() 
        if op.flags & IF_S:
            if op.opers[0].reg == 15:
                if (curmode != PM_sys and curmode != PM_usr):
                    self.setCPSR(self.getSPSR(curmode))
                else:
                    raise Exception("Messed up opcode...  adding to r15 from PM_usr or PM_sys")
            self.setFlag(PSR_C, e_bits.is_unsigned_carry(ures, dsize))
            self.setFlag(PSR_Z, not ures)
            self.setFlag(PSR_N, e_bits.is_signed(ures, dsize))
            self.setFlag(PSR_V, e_bits.is_signed_overflow(sres, dsize))

    def i_rsb(self, op):
        # Src op gets sign extended to dst
        #FIXME account for same operand with zero result for PDE
        src1 = self.getOperValue(op, 1)
        src2 = self.getOperValue(op, 2)
        Sflag = op.iflags & IF_PSR_S

        if src1 == None or src2 == None:
            self.undefFlags()
            return None

        res = self.intSubBase(src2, src1, Sflag, op.opers[0].reg)
        self.setOperValue(op, 0, res)

    def i_sub(self, op):
        # Src op gets sign extended to dst
        #FIXME account for same operand with zero result for PDE
        src1 = self.getOperValue(op, 1)
        src2 = self.getOperValue(op, 2)
        Sflag = op.iflags & IF_PSR_S

        if src1 == None or src2 == None:
            self.undefFlags()
            return None

        res = self.intSubBase(src1, src2, Sflag, op.opers[0].reg)
        self.setOperValue(op, 0, res)

    def i_eor(self, op):
        src1 = self.getOperValue(op, 1)
        src2 = self.getOperValue(op, 2)
        
        #FIXME PDE and flags
        if src1 == None or src2 == None:
            self.undefFlags()
            self.setOperValue(op, 0, None)
            return

        usrc1 = e_bits.unsigned(src1, 4)
        usrc2 = e_bits.unsigned(src2, 4)

        ures = usrc1 ^ usrc2

        self.setOperValue(op, 0, ures)

        curmode = self.getProcMode() 
        if op.iflags & IF_S:
            if op.opers[0].reg == 15:
                if (curmode != PM_sys and curmode != PM_usr):
                    self.setCPSR(self.getSPSR(curmode))
                else:
                    raise Exception("Messed up opcode...  adding to r15 from PM_usr or PM_sys")
            self.setFlag(PSR_C, e_bits.is_unsigned_carry(ures, 4))
            self.setFlag(PSR_Z, not ures)
            self.setFlag(PSR_N, e_bits.is_signed(ures, 4))
            self.setFlag(PSR_V, e_bits.is_signed_overflow(sres, 4))




    # Coprocessor Instructions
    def i_stc(self, op):
        cpnum = op.opers[0]
        coproc = self._getCoProc(cpnum)
        coproc.stc(op.opers)

    def i_ldc(self, op):
        cpnum = op.opers[0]
        coproc = self._getCoProc(cpnum)
        coproc.ldc(op.opers)

    def i_cdp(self, op):
        cpnum = op.opers[0]
        coproc = self._getCoProc(cpnum)
        coproc.cdp(op.opers)

    def i_mrc(self, op):
        cpnum = op.opers[0]
        coproc = self._getCoProc(cpnum)
        coproc.mrc(op.opers)

    def i_mrrc(self, op):
        cpnum = op.opers[0]
        coproc = self._getCoProc(cpnum)
        coproc.mrrc(op.opers)

    def i_mcr(self, op):
        cpnum = op.opers[0]
        coproc = self._getCoProc(cpnum)
        coproc.mrrc(op.opers)

    def i_mcrr(self, op):
        cpnum = op.opers[0]
        coproc = self._getCoProc(cpnum)
        coproc.mcrr(op.opers)




opcode_dist = \
[('and', 4083),#
 ('stm', 1120),#
 ('ldr', 1064),#
 ('add', 917),#
 ('stc', 859),#
 ('str', 770),#
 ('bl', 725),#
 ('ldm', 641),#
 ('b', 472),#
 ('ldc', 469),#
 ('tst', 419),#
 ('rsb', 196),#
 ('eor', 180),#
 ('mul', 159),
 ('swi', 128),
 ('sub', 110),#
 ('adc', 96),
 ('cdp', 74),#
 ('orr', 66),
 ('cmn', 59),
 ('mcr', 55),#
 ('stc2', 54),
 ('ldc2', 52),
 ('mrc', 49),#
 ('mvn', 47),
 ('rsc', 46),
 ('teq', 45),
 ('cmp', 41),
 ('sbc', 40),
 ('mov', 35),
 ('bic', 34),
 ('mcr2', 29),#
 ('mrc2', 28),#
 ('swp', 28),
 ('mcrr', 21),#
 ('mrrc', 20),#
 ('usada8', 20),
 ('qadd', 13),
 ('mrrc2', 10),#
 ('add16', 9),
 ('mla', 9),
 ('mcrr2', 7),#
 ('uqsub16', 6),
 ('uqadd16', 5),
 ('sub16', 5),
 ('umull', 4),
 ('uq', 3),
 ('smlsdx', 3),
 ('uhsub16', 3),
 ('uqsubaddx', 3),
 ('qdsub', 2),
 ('subaddx', 2),
 ('uqadd8', 2),
 ('ssat', 2),
 ('uqaddsubx', 2),
 ('smull', 2),
 ('blx', 2),
 ('smlal', 2),
 ('shsub16', 1),
 ('', 1),
 ('smlsd', 1),
 ('pkhbt', 1),
 ('revsh', 1),
 ('qadd16', 1),
 ('uqsub8', 1),
 ('ssub16', 1),
 ('usad8', 1),
 ('uadd16', 1),
 ('smladx', 1),
 ('swpb', 1),
 ('smlaldx', 1),
 ('usat', 1),
 ('umlal', 1),
 ('rev16', 1),
 ('sadd16', 1),
 ('sel', 1),
 ('sub8', 1),
 ('pkhtb', 1),
 ('umaal', 1),
 ('addsubx', 1),
 ('add8', 1),
 ('smlad', 1),
 ('sxtb', 1),
 ('sadd8', 1)]

