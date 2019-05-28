# -*- coding: utf-8 -*-
import rdflib
import sys
from xml.dom import minidom
import logging as log
import os

class browse_ontology(object):

    """
    """
    def get_elements(self,ontology):
        """
        Get owl elements by types in the ontology
        Check for each element if there are conditions to satisfy
        """
        
        self.xmldoc = minidom.parse(ontology)
        #What are generic abnormalities?
        self.get_omega(ontology)
        
        toplevel = self.xmldoc.getElementsByTagName("rdf:RDF")[0]
        self.rdfs_attributes = self.xmldoc.getElementsByTagName("rdf:RDF")[0].attributes.items()
        log.info(self.rdfs_attributes)
        individuals = toplevel.childNodes
        
        impl = minidom.getDOMImplementation()
        newdoc = impl.createDocument('rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"', 'rdf:RDF', None)
        self.top_element = newdoc.documentElement
        for att in self.rdfs_attributes:
            self.top_element.setAttribute(att[0],att[1])
        self.racer_minimal_abnormality_strategy(individuals)
        
        
    def get_omega(self,ontology):
        """
        Get markups in the ontology identifying omega 
        abnormalities.
        """
        self.xmldoc = minidom.parse(ontology)
        abnormalities = self.xmldoc.getElementsByTagName("ace:omega")
        for abnormality in abnormalities:
            log.info("Abnormality:"+str(abnormality))
        
        
    def racer_minimal_abnormality_strategy(self,elements):
        """
        identify the abnormalities expressed in ace tags
        Ensures that the consistency is preserved
        """
        self.newrule = 0
        self.acetags = self.xmldoc.getElementsByTagName("ace:Condition")
        log.info("Conditions: " + str(self.acetags))
        for element in elements:
            try:
                condition = element.getAttribute("ace:Condition")
            except:
                #Text nodes will cause exceptions
                log.debug("Text node encountered")
                continue
            if condition != "":
                log.info("Condition Encountered: " + str(condition))
                for tag in self.acetags:
                    log.info("Testing ace tag:" + str(tag))
                    idtag = tag.getAttribute("ace:name")
                    if idtag == condition:
                        query = tag.getElementsByTagName("ace:Query")[0].getAttribute("ace:abnormality")
                        negated =  tag.getElementsByTagName("ace:Query")[0].getAttribute("ace:negation")
                        log.info(query)
                        satisfied = self.test_condition(query, negated)
                        if satisfied == "unsatisfied":
                            #Integrate the element: the abnormality is not satisfied
                            log.info("Integrating the element")
                            self.top_element.appendChild(element)
                            self.integrated_Rules[element] = condition
                            self.newrule = 1
                            #Remember that this element is bound to a condition
                            self.dict_rules[element] = condition
                            #Check if integration of this new element does not
                            #fullfils omega abnormalities
                            if (self.test_omega()):
                                log.info("OMEGA VIOLATION RETURNED")
                                self.top_element.removeChild(element)
                                print ("AFTER REMOVAL OF \t"+str(element.toprettyxml(indent='\t'))+"\t->>"+str(self.top_element.toprettyxml(indent='\t')))
                                log.info("OMEGA VIOLATION CANCELED: element "+str(element.toprettyxml(indent='\t'))+" removed")
                                self.marked_Rules[element] = condition
                                self.integrated_Rules.pop(element, None)
                                break
                        if satisfied == "satisfied":
                            log.info("Rejecting the element:"+element.toprettyxml(indent='\t'))
                            #Reject the integration of the element in the ontology
                            #because the abnormality is satisfied.
                            #Remember that this element is bound to a condition
                            self.marked_Rules[element] = condition
                            self.integrated_Rules.pop(element, None)
                            break
            else:
                #Integrate the element
                log.debug("No condition")
                log.info("integrating: \n"+element.toprettyxml(indent='\t')+"\nin the ontology")
                self.top_element.appendChild(element)
                #Remember that this element is bound to a condition
                self.dict_rules[element] = condition
                #Check if integration of this new element does not
                #fullfils omega abnormalities
                self.newrule = 1
                if (self.test_omega()):
                    log.info("OMEGA VIOLATION RETURNED")
                    self.top_element.removeChild(element)
                    print ("AFTER REMOVAL OF \t"+str(element.toprettyxml(indent='\t'))+"\t->>"+str(self.top_element.toprettyxml(indent='\t')))
                    log.info("OMEGA VIOLATION CANCELED: element "+str(element.toprettyxml(indent='\t'))+" removed")
                    self.marked_Rules[element] = condition
                    self.newrule = 0
            while(self.newrule):
                log.info("A new rule has appeared")
                self.rules_marking()
                self.rules_unmarking()

    def rules_marking(self):
        """
        Algorithm for testing if rules integrated in the ontology now need to be marked
        """
        log.debug("Entering Rules Marking")
        newmark = 1
        while (newmark):
            mark = 0
            for key in self.integrated_Rules:
                log.info("Testing marking of rule:"+str(key.toprettyxml(indent='\t')))
                condition = self.integrated_Rules[key]
                log.info(condition)
                markxmldoc = minidom.parse(self.ontology)
                acetags = markxmldoc.getElementsByTagName("ace:Condition")
                for tag in acetags:
                    idtag = tag.getAttribute("ace:name")
                    if idtag == condition:
                        query = tag.getElementsByTagName("ace:Query")[0].getAttribute("ace:abnormality")
                        negated =  tag.getElementsByTagName("ace:Query")[0].getAttribute("ace:negation")
                        log.info(query)
                        satisfied = self.test_condition(query, negated)
                        if satisfied == "satisfied":
                            log.info("Rejecting the element:"+key.toprettyxml(indent='\t'))
                            #Reject the integration of the element in the ontology
                            #because the abnormality is satisfied.
                            #Remember that this element is bound to a condition
                            self.marked_Rules[key] = condition
                            self.top_element.removeChild(key)
                            self.integrated_Rules.pop(key, None)
                            mark = 1
                            self.rules_unmarking()
            newmark = mark
        log.debug("Exit from marking")

    def rules_unmarking(self):
        """
        Unmarks marked rules, see if they now can beintegrated in the ontology
        """
        log.debug("Entering Rules UNmarking")
        self.newrule = 0
        for key in self.marked_Rules:
            log.info("Integrating the element:"+str(key.toprettyxml(indent='\t')))
            self.top_element.appendChild(key)
            condition = self.marked_Rules[key]
            log.info("Integrating the element under condition:"+str(condition))
            #Check if integration of this new element does not
            #fullfils omega abnormalities
            if (self.test_omega() == 0):
                log.info("Unmarking --> NO OMEGA VIOLATION RETURNED")
                #acetags = self.xmldoc.getElementsByTagName("ace:Condition")
                log.info(str(self.acetags))
                unmarkxmldoc = minidom.parse(self.ontology)
                acetags = unmarkxmldoc.getElementsByTagName("ace:Condition")
                for tag in acetags:
                    idtag = tag.getAttribute("ace:name")
                    log.info("IDTAG -->"+str(idtag))
                    if idtag != condition:
                        log.info("Going TO NEXT IDTAG")
                        continue
                    if idtag == condition:
                        log.info("TESTING IDTAG")
                        query = tag.getElementsByTagName("ace:Query")[0].getAttribute("ace:abnormality")
                        negated =  tag.getElementsByTagName("ace:Query")[0].getAttribute("ace:negation")
                        log.info(query)
                        satisfied = self.test_condition(query, negated)
                        if satisfied == "unsatisfied":
                            #Integrate the element: the abnormality is not satisfied
                            log.info("Definitely integrating the element")
                            self.integrated_Rules[key] = condition
                            #Remember that this element is bound to a condition
                            self.dict_rules[key] = condition
                            log.info("A new rule has appeared by unmarking")
                            self.newrule = 1
                        if satisfied == "satisfied":
                            log.info("ABNORMALITY SATISFIED")
                            self.top_element.removeChild(key)
                            print ("AFTER REMOVAL OF \t"+str(key.toprettyxml(indent='\t'))+"\t->>"+str(self.top_element.toprettyxml(indent='\t')))
                            log.info("VIOLATION OF ABNORMALITY CANCELED: element "+str(key.toprettyxml(indent='\t'))+" removed")
                            self.newrule = 0
                            self.integrated_Rules.pop(key, None)
                            break
                if self.newrule == 1:
                    break
            else:
                log.info("OMEGA VIOLATION RETURNED")
                self.top_element.removeChild(key)
                print ("AFTER REMOVAL OF \t"+str(key.toprettyxml(indent='\t'))+"\t->>"+str(self.top_element.toprettyxml(indent='\t')))
                log.info("OMEGA VIOLATION CANCELED: element "+str(key.toprettyxml(indent='\t'))+" removed")
        if self.newrule == 1:
            self.marked_Rules.pop(key, None)
        log.info("EXIT UNMARKING")

    def test_omega(self):
        """
        Test if an abnormality in omega is satisfied.
        If it is the case, then the current rule is
        excluded from the ontology.
        """
        log.info("Entering OMEGA TEST")
        #First, save the current rules as an ontology.
        self.onto_file = open(self.onto_name,'w')
        self.onto_file.write(self.top_element.toprettyxml(indent='\t'))
        self.onto_file.close()
        #Second, test the condition on this ontology
        omegaxmldoc = minidom.parse(self.ontology)
        omegatag = omegaxmldoc.getElementsByTagName("ace:Omega")
        omega_ok = 0
        for tag in omegatag:
            local_ok = 1
            query = tag.getElementsByTagName("ace:Query")[0].getAttribute("ace:abnormality")
            negated =  tag.getElementsByTagName("ace:Query")[0].getAttribute("ace:negation")
            for q in query.split(";"):
                if q.replace(" ","")=="":
                    continue
                log.debug("OMEGA: testing -> "+q)
                satisfied = self.test_condition(q, negated)
                if satisfied == "satisfied":
                    log.debug("OMEGA: may have a pb on -> "+q)
                    pass
                else:
                    log.info("OMEGA: Not violating general abnormality")
                    local_ok = 0
                    break
            if local_ok == 1:
                omega_ok = 1
                log.info("OMEGA: fall")
        return omega_ok
                                                            
    def test_condition(self,in_query, negated):
        """
        Tests the condition to figure out wether or not the rule
        associated with the condition is to be integrated in ontology.
        """
        #First, save the current rules as an ontology.
        self.onto_file = open(self.onto_name,'w')
        self.onto_file.write(self.top_element.toprettyxml(indent='\t'))
        self.onto_file.close()
        #Second, test the condition on this ontology
        self.g = rdflib.Graph()
        self.g.parse(self.onto_name)

        query_string = ""
        for att in self.rdfs_attributes:
            try:
                query_string += "PREFIX "+att[0].split(":")[1]+": <"+att[1]+">\n"
            except:
                query_string += "PREFIX "+att[0]+": <"+att[1]+">\n"

        query_string += "SELECT ?object WHERE {\n"
        log.info(in_query)
        splitted_in_query = in_query.split(";")
        for q in splitted_in_query:
            try:
                log.debug(q)
                log.debug("splitte par virgule: "+str(q.split(",")))
                subject = q.split(",")[0]
                inverse = 0
                if subject[0] == "!":
                    log.debug("inversion")
                    inverse = 1
                    subject = subject.replace("!","")
                log.debug("sujet: "+subject)
                predicate = q.split(",")[1]
                log.debug("predicat: "+predicate)
                obj = q.split(",")[2]
                log.debug("objet: "+obj)
                query_string += "base:"+subject +" " + predicate + " ?object .\n"
                query_string += """FILTER regex(str(?object), "%s","i") .}\n""" % (obj)
                log.info("Query string: "+str(query_string))
            except Exception as e:
                log.warning(str(e))
                continue
            log.info("Sending Query")
            qres = self.g.query(query_string)
            log.info("len of query is: "+str(len(qres)))
            #finally, return whereas the condition is fulfilled or not
            result = ""
            if len(qres) == 0:
                #The query has no result.
                if negated == "negative":
                    #No result, and abnormality satisfied if there is
                    #no result because we test negation
                    result = "satisfied"
                if negated ==  "no negation":
                    #No result, abnormailty unsatisfied because
                    #we test fulfillment
                    result = "unsatisfied"
            else:
                 #The query has one/some results.
                if negated == "negative":
                    result ="unsatisfied"
                if negated ==  "no negation":
                    result ="satisfied"
        if inverse == 0:
            return result
        if inverse == 1:
            if result == "statisfied":
                return "unsatisfied"
            if result == "unsatisfied":
                return"satisfied"
        
    def __init__(self,ontology):
        """
            Constructeur de la classe
        """
        os.system("rm ace.log")
        self.onto_name = ontology+"_AceVerified.owl"
        self.ontology = ontology
        os.system("rm "+self.onto_name)
        log.basicConfig(filename='ace.log',level=log.DEBUG,format='%(levelname)s:%(asctime)s %(message)s ')
        log.info(ontology)
        self.dict_rules={}
        self.marked_Rules = {}
        self.integrated_Rules = {}
        #List of abnormalities applying for all rules.
        self.omega = []
        self.get_elements(ontology)
        #Finally save the current rules as an ontology.
        self.onto_file = open(self.onto_name,'w')
        self.onto_file.write(self.top_element.toprettyxml(indent='\t'))
        self.onto_file.close()
        
test =  browse_ontology(sys.argv[1])
