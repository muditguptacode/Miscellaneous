import os, sys, time, re

class g:
    auto_set = True
    start_byte = ""
    second_byte = ""
    third_byte = ""
    start = ""
    end = ""
    arg_list = ""
    logfile = os.path.splitext(os.path.basename(__file__))[0] + "-Log.txt"

def set_dns(dns_primary, dns_secondary=""):
 if (dns_primary=="auto"):
  os.system("netsh interface ipv4 set dns \"Wireless Network Connection\" source = dhcp")
  return
 os.system("netsh interface ipv4 set dns \"Wireless Network Connection\" static " + dns_primary +" primary validate=no")
 os.system("netsh interface ipv4 add dns \"Wireless Network Connection\" "+ dns_secondary +" index=2 validate=no")
    
def tail( f, window=20 ):
    BUFSIZ = 1024
    f.seek(0, 2)
    bytes = f.tell()
    size = window
    block = -1
    data = []
    while size > 0 and bytes > 0:
        if (bytes - BUFSIZ > 0):
            # Seek back one whole BUFSIZ
            f.seek(block*BUFSIZ, 2)
            data.append(f.read(BUFSIZ))
        else:
            # file too small, start from begining
            f.seek(0,0)
            # only read what was not read
            data.append(f.read(bytes))
        linesFound = data[-1].count('\n')
        size -= linesFound
        bytes -= BUFSIZ
        block -= 1
    return '\n'.join(''.join(data).splitlines()[-window:])


def get_last_run_options():
    
    logfile = os.path.join(os.path.dirname(sys.argv[0]), g.logfile)
    args = 0
    if os.path.isfile(logfile):
        f = file(logfile, 'r')
        lines = tail(f, 1)
        print "Last successful run: " + lines 
        args = re.search("\[(.*)\]", lines).group(1)
    
    return args

def get_args(argv = sys.argv): 
 
 for (index, args) in enumerate(argv):
  
  if (args == "--reset" or args == "-r"):
   os.system("netsh interface ipv4 set dns \"Wireless Network Connection\" source=dhcp")
   os.system("netsh interface ipv4 set address \"Wireless Network Connection\" source=dhcp")
   sys.exit(0)
  elif (args == "--last-run" or args == "-l"):
   arg_list = get_last_run_options()
   if arg_list:
       g.arg_list = arg_list
       args_f = g.arg_list.split()
       get_args(args_f)
       break
  elif (args == "--googledns" or args == "-gdns"):
   set_dns("8.8.8.8", "8.8.4.4")
  elif (args == "--autodns" or args == "-adns"):
   set_dns("auto")
  elif (args == "--exit" or args == "-q"):
   sys.exit(0)
  elif (args == "--start_iter" or args == "-s"):
   g.start = int(argv[index+1])
  elif (args == "--end_iter" or args == "-e"):
   g.end = int(argv[index+1])
  elif (args == "--start_byte" or args == "-b1"):
   g.start_byte = argv[index+1]   
  elif (args == "--second_byte" or args == "-b2"):
   g.second_byte = argv[index+1]
  elif (args == "--third_byte" or args == "-b3"):
   g.third_byte = argv[index+1]


def main():
 print "\nCommand : " + str(sys.argv) + "\n"
 
 if (len(sys.argv) < 2):
  if (g.auto_set): get_args(["-l"])
 else : get_args()
 
 if (g.arg_list == ""):
  for arg in sys.argv[1:]:
   g.arg_list = g.arg_list + arg + " "
 
 if (g.start_byte == ""):
  g.start_byte = 10
 if (g.second_byte == ""):
  g.second_byte = 89
 if (g.third_byte == ""): 
  g.third_byte = 3
 
 subnet = "255.255.252.0"
 gateway = "10.89.0.1"
 dns_primary = "8.8.8.8"
 dns_secondary = "8.8.4.4"
 ping_addr = "google.com"
 
 if (g.start == ""):
  g.start = 0
 if (g.end == ""):
  g.end = 255

 x = range(g.start,g.end)
 for last_byte in x:
  ip_addr = str(g.start_byte) + "." + str(g.second_byte) + "." + str(g.third_byte) + "." + str(last_byte)
  print "\nChecking " + ip_addr
  output = os.system("netsh interface ipv4 set address \"Wireless Network Connection\" static " + ip_addr + " " + subnet + " " + gateway + " & sleep 3 & ping " + ping_addr + " & sleep 3 & ping " + ping_addr)
  if (output == 0):
      print "Success : " + ip_addr
      f = file(os.path.dirname(sys.argv[0]) + "/" + g.logfile, 'a+')
      try:
          f.seek(-2000, 2)
      except:
          f.seek(0, 0)
      log_recent = f.readlines()
      if not re.search(time.strftime("%x"), str(log_recent)):
          f.write("\n\n" + time.strftime("%x") + ":\n")
      f.write("\n" + time.strftime("%X") + ": " + ip_addr + " [" + g.arg_list + "]")
      f.close()
      return
 print "Failed. Unable to determine any working IP address"
  
if __name__ == "__main__":
 main()