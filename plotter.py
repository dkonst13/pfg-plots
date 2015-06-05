#!/usr/bin/env python

import sys
import os
import sqlite3
import ROOT
import subprocess

ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(True)
ROOT.TH1.AddDirectory(False)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

def plot2D(dbh, status = "ENABLED", ytable = "TT_FE_STATUS_BITS"):
  if status.__class__ != list:
    status = [status]
  height = dbh.execute("select count(distinct TT_id) from TT_FE_STATUS_BITS where status = {0}".format(" or status = ".join(["'{0}'".format(q) for q in status]))).fetchone()[0]
  minwidth = dbh.execute("select min(run_num) from runs").fetchone()[0]
  maxwidth = dbh.execute("select max(run_num) from runs").fetchone()[0]
  width = maxwidth - minwidth
  #cname = dbh.execute("select name from plots where ytable = 'runs' and xtable = '{0}' and key = '{1}'".format(ytable, status)).fetchone()[0]
  cname = "+".join(status)
  c = ROOT.TCanvas(cname, cname)
  hist = ROOT.TH2F (cname, cname, width + 1, minwidth, maxwidth + 1, height, 1, height)
  hist.SetXTitle("Runs")
  hist.SetYTitle("TT")
  hist.SetMinimum(0)
  hist.SetMaximum(100)
  cur = dbh.cursor()
  xidx = 1
  for x in sorted([i[0] for i in dbh.execute("select distinct run_num from {0}".format(ytable))]):
    yidx = 1
    for y in sorted([j[0] for j in dbh.execute("select distinct TT_id from {0} where status = {1}".format(ytable, " or status = ".join(["'{0}'".format(q) for q in status])))]):
      try:
        tt = cur.execute("select tt, det, sm from TT_IDS where tt_id = {0}".format(y)).fetchone()
        ttname = "{1}{2:+03d}: TT{0}".format(tt[0], tt[1], tt[2])
        sum = cur.execute("select sum(value) from {0} where run_num = {1} and tt_id = {2}".format(ytable, x, y)).fetchone()[0]
        valarr = cur.execute("select sum(value) from {0} where run_num = {1} and tt_id = {2} and (status = {3})".format(ytable, x, y,  " or status = ".join(["'{0}'".format(q) for q in status]))).fetchone()
        if valarr[0] is not None:
          val = valarr[0] * 100 / float(sum)
        else:
          val = 0
        if val > 100:
          print "!!! wrong logic !!!"
          sys.exit(1)
        print " run: {0:7d}, tt: {1:15s}, status: {2:40s}, value: {3}".format(x, ttname, "+".join(status), val)
        hist.SetBinContent(xidx, yidx, val)
      except Exception as e:
        print "Skip: ", str(e)
      hist.GetYaxis().SetBinLabel(yidx, ttname)
      yidx += 1
    hist.GetXaxis().SetBinLabel(xidx, str(x))
    xidx += 1
  hist.LabelsDeflate()
  hist.LabelsOption("v", "X")
#  c.Draw()
  hist.Draw("colz")
  c.Update()
  c.SaveAs("plots/" + "_".join(status) + ".png")

def download(url, localpath):
  """Downloads file with wget.
    File is first downloaded under a name 'tmpfile' and then renamed: the
    renaming operation is atomic, so the file is either fully downloaded or not
    downloaded at all.
  """
  for d in ['downloads', 'plots']:
    if not os.access(d, os.X_OK):
      os.mkdir(d)
  if os.access(localpath, os.R_OK):
    return  # file already downloaded
  tmpfile = os.path.join(os.path.dirname(localpath), 'tmpfile')
  keypath  = os.path.join(os.getenv('HOME'), '.globus/userkey.pem')
  certpath = os.path.join(os.getenv('HOME'), '.globus/usercert.pem')
  # run wget
  ret = subprocess.call(['wget', '-q', '--no-check-certificate',
                         '--certificate=' + certpath,
                         '--private-key=' + keypath, url, '-O', tmpfile],
                        stdout=sys.stdout, stderr=sys.stderr)
  if ret != 0:
      sys.exit(1)
  # atomic rename
  os.rename(tmpfile, localpath)

def filldb(dbh, run, table = "TT_FE_STATUS_BITS"):
  pathfmt = 'https://cmsweb.cern.ch/dqm/online/data/browse/ROOT/{0:05d}xxxx/{1:07d}xx/DQM_V0001_{3}_R{2:09d}.root'
  url = pathfmt.format(int(run/10000), int(run/100), run, 'Ecal')
  path = os.path.join('downloads', os.path.basename(url))
  download(url, path)
  rootfile = 'downloads/' + os.path.basename(url)
  print "Processing file ", rootfile
  f = ROOT.TFile(rootfile)
  print "select * from runs where run_num = {0} and root_file = '{1}'".format(run, rootfile)
  if len(dbh.execute("select * from runs where run_num = {0} and root_file = '{1}'".format(run, rootfile)).fetchall()) != 0:
    print "Finished"
    return dbh
  dbh.execute("insert into runs values ({0}, '{1}', '{2}')".format(run, rootfile, 'https://cmsweb.cern.ch/dqm/online/data/browse/ROOT/{0:05d}xxxx/{1:07d}xx/DQM_V0001_{3}_R{2:09d}.root'.format(int(run/10000), int(run/100), run, 'Ecal') ))
  cur = dbh.cursor()
  for (det, maxfe) in zip(["EB", "EE"], [18, 8]):
    for fe in range(-maxfe, maxfe + 1):
      if fe == 0 :
        continue
      print " {0}{1:+03d} ...".format(det, fe)
      fmt = '/DQMData/Run {0}/Ecal{3}/Run summary/{1}StatusFlagsTask/FEStatus/{1}SFT front-end status bits {1}{2:+03d}'
      festatus = f.Get(fmt.format(run, det, fe, 'Barrel' if det == 'EB' else 'Endcap'))
      for tt in range(1, festatus.GetNbinsX() + 1):
        if len(cur.execute("select tt_id from TT_IDS where tt = {0} and det = '{1}' and sm = {2}".format(tt, det, fe)).fetchall()) == 0:
          cur.execute("insert or fail into TT_IDS (tt, det, sm) values ({0}, '{1}', {2})".format(tt, det, fe))
        for status in range(festatus.GetNbinsY()):
          if festatus.GetBinContent(tt, status + 1) > 0:
            label = festatus.GetYaxis().GetBinLabel(status + 1)
            value = festatus.GetBinContent(tt, status + 1)
            sql = "insert into {table} values ({run}, '{status}', {value}, {tt_id})".format(table = table, run = run, status = label, value = value, tt_id = cur.execute("select tt_id from TT_IDS where det = '{0}' and sm = {1} and tt = {2}".format(det, fe, tt)).fetchone()[0] )
            cur.execute(sql)
  dbh.commit()
  print "Finished"
  return dbh

dbh = sqlite3.connect(sys.argv[1])

for i in open('runs.list','r').readlines():
  for k in i.split():
    k = int(k)
    try:
      dbh = filldb(dbh, k)
    except:
      pass
dbh.commit()

errorcodes = [c[0] for c in dbh.execute("select distinct status from TT_FE_STATUS_BITS") if c[0] != "ENABLED" and c[0] != "SUPPRESSED"]

for ec in errorcodes:
  plot2D(dbh, ec)

# additional combo
plot2D(dbh, ["LINKERROR", "TIMEOUT", "HEADERERROR"])
plot2D(dbh, ["LINKERROR", "TIMEOUT"] )
plot2D(dbh, ["LINKERROR", "HEADERERROR"])
