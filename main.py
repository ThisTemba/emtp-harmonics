import csv
import os
import sys
import time

import numpy as np
from lxml import etree
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText
from matplotlib.ticker import MultipleLocator


#  node names are bus names but each bus name gets a suffix of a, b, or c
def getNodeNames(busNames):
    nodeNames = []
    for bus in busNames:
        nodeNames.append(bus + "a")
        nodeNames.append(bus + "b")
        nodeNames.append(bus + "c")
    return nodeNames


def getColumnIndex(columnName, table):
    rows = table.findall("tr")
    headings = [col.text for col in rows[1].findall("td")]
    return headings.index(columnName)


def getXmlData(filename):
    print("input file:", filename)
    print("Parsing HTML. This may take a bit...")
    parser = etree.HTMLParser()
    tree = etree.parse(filename, parser)
    xmlData = tree.getroot()
    return xmlData


def getFreqs(xmlData):
    freqs = []
    for header in xmlData.findall(".//h1"):
        headerStr = header.text
        thingsToRemove = ["Solution", "frequency", ":", " "]
        for thing in thingsToRemove:
            headerStr = headerStr.replace(thing, "")
        freq = int(headerStr)
        freqs.append(freq)
    return freqs


def getNodeVoltageDict(xmlData, busNames):
    freqs = getFreqs(xmlData)
    tables = xmlData.findall(".//table[@id='NodeVoltagesTable']")
    NodeIndex = getColumnIndex("Node", tables[0])
    ModuleVoltageIndex = getColumnIndex("Module (V)", tables[0])
    nodeVoltageDict = {}
    for (tableIndex, table) in enumerate(tables):
        nodeVoltages = []  # list will hold pairs of (TPSS node: Voltage)
        rows = table.findall("tr")
        for row in rows:
            cells = row.findall("td")
            node = cells[NodeIndex].text
            if node in getNodeNames(busNames):
                moduleVoltage = cells[ModuleVoltageIndex].text
                nodeVoltages.append((node, moduleVoltage))
        freq = freqs[tableIndex]
        nodeVoltageDict[freq] = nodeVoltages
    nodeVoltageDict = dict(sorted(nodeVoltageDict.items()))
    return nodeVoltageDict


def getFundamentalVoltage(nodeVoltageDictionary, node):
    filterResult = filter(lambda x: x[0] == node, nodeVoltageDictionary[60])
    v_fund_rms = list(filterResult)[0][1]
    return v_fund_rms


def getIHDandTHD(nodeVoltageDictionary):
    output = {}
    for freq in nodeVoltageDictionary:
        if freq == 60:
            continue
        harmonic = int(freq / 60)
        for [node, voltage] in nodeVoltageDictionary[freq]:
            if node not in output:
                output[node] = {"thd": 0, "ihd": {}}

            voltage = float(voltage)
            v_at_60hz = getFundamentalVoltage(nodeVoltageDictionary, node)
            output[node]["thd"] += voltage**2
            output[node]["ihd"][harmonic] = voltage / v_at_60hz

    for node in output:
        v_at_60hz = getFundamentalVoltage(nodeVoltageDictionary, node)
        output[node]["thd"] = output[node]["thd"] ** 0.5 / v_at_60hz
    return output


def getFundamentalVoltage(nodeVoltageDictionary, node):
    filterResult = filter(lambda x: x[0] == node, nodeVoltageDictionary[60])
    v_fund_rms = float(list(filterResult)[0][1])
    return v_fund_rms


def getIHDandTHD(nodeVoltageDictionary):
    output = {}
    for freq in nodeVoltageDictionary:
        if freq == 60:
            continue
        harmonic = int(freq / 60)
        for [node, voltage] in nodeVoltageDictionary[freq]:
            if node not in output:
                output[node] = {"thd": 0, "ihd": {}}

            voltage = float(voltage)
            v_at_60hz = getFundamentalVoltage(nodeVoltageDictionary, node)
            output[node]["thd"] += voltage**2
            output[node]["ihd"][harmonic] = voltage / v_at_60hz

    for node in output:
        v_at_60hz = getFundamentalVoltage(nodeVoltageDictionary, node)
        output[node]["thd"] = output[node]["thd"] ** 0.5 / v_at_60hz
    return output


def getLabelsAndValues(a, b, c):
    labels = a["ihd"].keys()
    avalues = np.array(list(a["ihd"].values())) * 100
    bvalues = np.array(list(b["ihd"].values())) * 100
    cvalues = np.array(list(c["ihd"].values())) * 100
    return labels, avalues, bvalues, cvalues


def addBars(avalues, bvalues, cvalues, x, width, ax):
    ax.bar(x - width, avalues, width, label="Phase A")
    ax.bar(x, bvalues, width, label="Phase B")
    ax.bar(x + width, cvalues, width, label="Phase C")


def addTextBox(a, b, c, nodeGroup, ax):
    textstr = "\n".join(
        [
            "Total Harmonic Distortion",
            nodeGroup + " Phase A THD = " + str(round(a["thd"] * 100, 2)) + "%",
            nodeGroup + " Phase B THD = " + str(round(b["thd"] * 100, 2)) + "%",
            nodeGroup + " Phase C THD = " + str(round(c["thd"] * 100, 2)) + "%",
        ]
    )

    # place a text box in upper left in axes coords
    anchored_text = AnchoredText(textstr, loc="upper right", prop={"size": 13})
    ax.add_artist(anchored_text)


def addLegend(fig, ax):
    ax.legend()
    plt.legend(
        bbox_to_anchor=(0.5, 0.05),
        loc="upper center",
        bbox_transform=fig.transFigure,
        ncol=4,
    )


def plotBarChart(a, b, c, nodeGroup, outFolder):
    labels, avalues, bvalues, cvalues = getLabelsAndValues(a, b, c)
    nodeGroup = nodeGroup.replace("_", " ")

    x = np.arange(len(labels))  # the label locations
    width = 0.2  # the width of the bars
    plt.rcParams["figure.figsize"] = (12, 6)

    # plot bar chart
    fig, ax = plt.subplots()
    addBars(avalues, bvalues, cvalues, x, width, ax)

    # Axis Labels
    ax.set_ylabel("% of 115 kV Nominal Voltage (%)", fontweight="bold")
    ax.set_xlabel("Harmonic", fontweight="bold")

    # Title
    title = "PCEP TPS1 Voltage harmonic Distortion - " + nodeGroup
    configName = "C FMC-SJB Out"
    subtitle = "Cal001 Train Config " + configName
    plt.suptitle(title, fontsize=18, fontweight="bold")
    ax.set_title(subtitle, fontsize=14, fontweight="bold")

    # Ticks & Gridlines
    ax.set_xticks(x, labels, fontsize=9)

    yticks = np.arange(0, 1.5 + 0.3, 0.3)
    ylabels = [str(round(i, 1)) + "%" for i in yticks]
    ax.set_yticks(yticks, ylabels)
    ax.yaxis.set_minor_locator(MultipleLocator(0.1))
    ax.tick_params(which="minor", length=4, color="grey")
    ax.grid(which="major", linewidth=0.3, color="black", axis="y")

    # Legend
    addLegend(fig, ax)

    # Axis Limits
    plt.ylim(0, 1.5)
    plt.xlim(min(x) - 0.5, max(x) + 0.5)

    # Textbox
    addTextBox(a, b, c, nodeGroup, ax)

    # Save and Show
    fig.tight_layout()
    fig.savefig(outFolder + "/" + title + ".jpg", bbox_inches="tight", dpi=300)


def getNodeGroups(harmonicDistortions):
    nodeGroups = []
    for node in harmonicDistortions:
        if node[:-1] not in nodeGroups:
            nodeGroups.append(node[:-1])
    return nodeGroups


def plotAllBarCharts(harmonicDistortions, outFolder):
    nodeGroups = getNodeGroups(harmonicDistortions)
    if not os.path.exists(outFolder):
        os.makedirs(outFolder)
    for nodeGroup in nodeGroups:
        a = harmonicDistortions[nodeGroup + "a"]
        b = harmonicDistortions[nodeGroup + "b"]
        c = harmonicDistortions[nodeGroup + "c"]
        plotBarChart(a, b, c, nodeGroup, outFolder)


def getCsvFilename(inputFilename):
    basename = os.path.basename(inputFilename)
    return os.path.splitext(basename)[0] + ".csv"


def write_to_csv(input_dict, inputFilename):
    print("Now converting to a usable csv file.")
    # Get array of THDs for 6 TPSS 3PH buses
    dictOfTHD = {}
    for (freq, moduleVoltagePairs) in input_dict.items():
        thd_list = []
        for pair in moduleVoltagePairs:
            (node, voltage) = pair
            voltage = float(voltage)
            thd_list.append(voltage)
        dictOfTHD[freq] = thd_list

    # collect all the node names as the first column
    # TODO: this is a hack, the 0 key sorts into the first column, but the column name should really be "Node"
    dictOfTHD[0] = [node for (node, _) in list(input_dict.values())[0]]

    # Write to csv file to make graphs in xls
    direct = os.getcwd()
    outFolder = "voltage_csv_output"
    if not os.path.exists(outFolder):
        os.makedirs(outFolder)
    csvFilename = getCsvFilename(inputFilename)
    a_file = open(direct + "/" + outFolder + "/" + csvFilename + ".csv", "w")
    keys = sorted(dictOfTHD.keys())
    with a_file as outfile:
        writer = csv.writer(outfile)
        writer.writerow(keys)
        writer.writerows(zip(*[dictOfTHD[key] for key in keys]))
    a_file.close()
    print("Printed table of voltages in a csv here: " + outFolder)


def main():
    # BUS_NAMES = [
    #     "FIB",
    #     "FMC",
    #     "DUA_115",
    #     "DVR_13_RaGT1",
    #     "DVR_13_RbGT2",
    #     "DVR_13_RaST3",
    #     "KRS_115",
    #     "KRS_60",
    # ]
    BUS_NAMES = ["East_Grand"]
    # NOTE: make sure these BUS_NAMES are the ones you want to extract from the html file

    start_time = time.time()
    # read file name (input to program)
    inputFilename = r" ".join(sys.argv[1 : len(sys.argv)])
    xmlData = getXmlData(inputFilename)
    nodeVoltageDict = getNodeVoltageDict(xmlData, BUS_NAMES)
    ThdAndIhd = getIHDandTHD(nodeVoltageDict)
    plotAllBarCharts(ThdAndIhd, "histograms")
    write_to_csv(nodeVoltageDict, inputFilename)

    # show how long the program took to run
    print(f"--- Total runtime: {time.time() - start_time:.2f} seconds ---")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        filename = sys.argv[1]
    main()
