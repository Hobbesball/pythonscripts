#this script takes a JSON harvest from an OAI endpoint as input, gets rid of the wrappers of every item and loads the XML into an output.xml file. It then takes four values from the raw XML: the title of the work, the object number, the date (displaydate, not earliest/latest), and the creator of the work. Those fields are exported into a CSV file

#import JSON to extract XML from Camandu's LIDO export
import json
#import XML ElementTree to extract the needed fields from the XML file
import xml.etree.ElementTree as ET
#import CSV to be able to write the elementtree output to CSV
import csv

#take catmandu JSON
with open('harvest1.json') as json_data:
    d = json.load(json_data)
    print(type(d))
    #print info to console
    print(type(d[0]))
    e = d[:500]
    #delete illegal XML characters
    deleteslashes = str.maketrans(dict.fromkeys("\\"))
    #open new XML file
    with open('output.xml', 'w') as output:
        #create root element called data
        output.write("<data>")
        #input item XML in element called item
        for index in range(len(e)):
            metadata = e[index]['_metadata'].translate(deleteslashes)
            output.write("<item>"+metadata+"</item>")
            #close xml file
        output.write("</data>")
        print("wrote ",len(e)," XML items to output.xml")
        
#declare lido namespaces
ns = {"lido": "http://www.lido-schema.org", "xlink":"http://www.w3.org/1999/xlink", "gml":"http://www.opengis.net/gml"}     
#parse the XML
tree = ET.parse('output.xml')
root = tree.getroot()
#topen CSV file that will be written to
with open('LIDOoutput.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL,)
    #create CSV header
    writer.writerow(['title','object_number','creation_date','creator(s)'])
    #initialise counter so we can print out how many rows were written at the end
    childamount = 0
    #start iterating over every XML item
    for child in root:
        childamount += 1
        csvrow = []
        actorlist = []
        titlelist = []
        #find all titles that have the qualifier = preferred. Append those to each other with an ampersand, so it's clear that they are different titles and can easily be taken apart again with a find and replace or split 
        for title in child.findall('.//lido:titleSet/lido:appellationValue[@lido:pref="preferred"]', ns):
            titlelist.append(title.text)
        titlelist = ' & '.join(titlelist)
        csvrow.append(titlelist)
        #there will only be one object number, find it and append it to the row
        for objectnumber in child.findall('.//lido:workID[@lido:type="objectnummer"]', ns):
            csvrow.append(objectnumber.text)
        #there will only be one display date, find it and append it to the row
        for date in child.findall('.//lido:eventDate/lido:displayDate', ns):
            csvrow.append(date.text)
        #find all creators that have the qualifier = preferred. Append those to each other with an ampersand, so it's clear that they are different titles and can easily be taken apart again with a find and replace or split 
        for creator in child.findall('.//lido:actorInRole', ns):
            actor = creator.find('lido:actor/lido:nameActorSet/lido:appellationValue[@lido:pref="preferred"]', ns)
            #see if there is a qualifier that needs to be added in front of the actor's appellation value. If it exists, append it to the actor
            actorattr = creator.find('lido:attributionQualifierActor', ns)
            if actorattr is None:
                actorlist.append(actor.text)
            else:
                actorlist.append(actorattr.text + " " + actor.text)
        actorlist = ' & '.join(actorlist)
        csvrow.append(actorlist)
        print("wrote ",csvrow," to csv")
        #write the row to the CSV file and go to next XML item
        writer.writerow(csvrow)
    #at the end of iterating over every XML item, print how many items were written to CSV
    print("wrote ",childamount, " lines to CSV" )        