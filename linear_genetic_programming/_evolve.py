from linear_genetic_programming._instruction import Instruction
from linear_genetic_programming._population import Population
from linear_genetic_programming._genetic_operations import GeneticOperations
import numpy as np
import copy


class Evolve:
    # np.random.seed(0)

    def __init__(self, tournamentSize, maxGeneration, population):
        self.tournamentSize = tournamentSize
        self.maxGeneration = maxGeneration
        self.p = population

    # return a copy of winner program
    # Binary tournament selection is most often used.
    def twoTournamentSelectionReturnProgram(self):
        if self.tournamentSize*2 > len(self.p.population):
            raise ValueError("2 * Tournament size cannot be larger than population")
        winner1 = None
        winner2 = None
        rand1, rand2 = np.split(np.random.choice(len(self.p.population), self.tournamentSize*2, replace=False), 2)
        for i in range(self.tournamentSize):
            cur = self.p.population[rand1[i]]
            if winner1 == None or cur.fitness > winner1.fitness:
                winner1 = cur
        for j in range(self.tournamentSize):
            cur = self.p.population[rand2[j]]
            if winner2 == None or cur.fitness > winner1.fitness:
                winner2 = cur
        return copy.deepcopy(winner1), copy.deepcopy(winner2)

    def twoTournamentSelectionReturnIndex(self):
        '''
        :return:  winner1 index, winner2 index, loser1 index, loser2 index
        '''
        winner1, winner2, loser1, loser2 = None, None, None, None
        win1Idx, win2Idx, loser1dx, loser2dx = 0, 0, 0, 0
        rand1, rand2 = np.split(np.random.choice(len(self.p.population), self.tournamentSize*2, replace=False), 2)
        for i in range(self.tournamentSize):
            cur = self.p.population[rand1[i]]
            if winner1 == None or cur.fitness > winner1.fitness:
                winner1 = cur
                win1Idx = rand1[i]
            if loser1 == None or cur.fitness < loser1.fitness:
                loser1 = cur
                loser1dx = rand1[i]
        for i in range(self.tournamentSize):
            cur = self.p.population[rand2[i]]
            if winner2 == None or cur.fitness > winner2.fitness:
                winner2 = cur
                win2Idx = rand2[i]
            if loser2 == None or cur.fitness < loser2.fitness:
                loser2 = cur
                loser2dx = rand2[i]
        return win1Idx, win2Idx, loser1dx, loser2dx

    def displayStatistics(self, g, bestIndividual, randomSamplingSize):
        print("Gen " + str(g) + ": Best indv=" + str(round(bestIndividual.fitness, 2))
                +", CE=" + str(bestIndividual.classificationError)
                + ", Pop avg=" + str(round(self.p.getAverageFitness(), 2))
                + ", RanSample Sz=" + str(randomSamplingSize) )

    def evolveGeneration(self, pRegMut, pMicro, pMacro, pConst, pCrossover, numberOfVariable, numberOfInput, numberOfOperation,
                         numberOfConstant, register, pInsert, maxProgLength, minProgLength,
                         X_train, y_train, fitnessThreshold, showGenerationStat, randomSampling, evolutionStrategy):
        if evolutionStrategy == "population":
            return self.populationalEvolution(pRegMut, pMicro, pMacro, pConst, pCrossover, numberOfVariable, numberOfInput,
                                  numberOfOperation, numberOfConstant, register, pInsert, maxProgLength, minProgLength,
                                  X_train, y_train, fitnessThreshold, showGenerationStat, randomSampling)
        elif evolutionStrategy == "steady state":
            return self.stedyStateEvolution(pRegMut, pMicro, pMacro, pConst, pCrossover, numberOfVariable, numberOfInput,
                                  numberOfOperation, numberOfConstant, register, pInsert, maxProgLength, minProgLength,
                                  X_train, y_train, fitnessThreshold, showGenerationStat)
        else:
            raise ValueError("Please choose between populational or steady state")

    def stedyStateEvolution(self, pRegMut, pMicro, pMacro, pConst, pCrossover, numberOfVariable, numberOfInput, numberOfOperation,
                         numberOfConstant, register, pInsert, maxProgLength, minProgLength,
                         X_train, y_train, fitnessThreshold, showGenerationStat):
        '''
        Implements "Linear genetic programming" Algorithm 2.1
        '''
        self.p.evaluatePopulation(numberOfVariable, register, X_train, y_train)
        bestIndividual = self.p.getBestIndividual()

        for g in range(self.maxGeneration):

            for _ in range(len(self.p.population)//2):
                # Perform two fitness tournaments
                win1Idx, win2Idx, loser1Idx, loser2Idx = self.twoTournamentSelectionReturnIndex()

                winner1 = copy.deepcopy(self.p.population[win1Idx])
                winner2 = copy.deepcopy(self.p.population[win2Idx])

                # Modify the two winners by one or more variation operators with certain probabilities(cross over)
                if np.random.random_sample() < pCrossover:
                    winner1, winner2 = GeneticOperations.simpleCrossover(winner1, winner2)
                # Mutation
                if np.random.random_sample() < pMacro:
                    randomInstr = Instruction(numberOfOperation, numberOfVariable, numberOfInput, numberOfConstant, pConst)
                    GeneticOperations.macroMutation(winner1, pInsert, maxProgLength, minProgLength, randomInstr)
                if np.random.random_sample() < pMacro:
                    randomInstr = Instruction(numberOfOperation, numberOfVariable, numberOfInput, numberOfConstant, pConst)
                    GeneticOperations.macroMutation(winner2, pInsert, maxProgLength, minProgLength, randomInstr)
                if np.random.random_sample() < pMicro:
                    GeneticOperations.microMutation(winner1, pRegMut, pConst, numberOfVariable, numberOfInput, numberOfOperation,
                                       numberOfConstant)
                if np.random.random_sample() < pMicro:
                    GeneticOperations.microMutation(winner2, pRegMut, pConst, numberOfVariable, numberOfInput, numberOfOperation,
                                       numberOfConstant)

                # update bestIndividual
                winner1.evaluate(numberOfVariable, register, X_train, y_train)
                winner2.evaluate(numberOfVariable, register, X_train, y_train)

                if winner1.fitness > bestIndividual.fitness:
                    bestIndividual = winner1
                if winner2.fitness > bestIndividual.fitness:
                    bestIndividual = winner2

                self.p.population[loser1Idx] = winner1
                self.p.population[loser2Idx] = winner2

            if showGenerationStat:
                self.displayStatistics(g, bestIndividual, randomSamplingSize="no")

            # if the solution has been found, end the loop
            if bestIndividual.fitness >= fitnessThreshold:
                return bestIndividual

            # self.p.displayPopulationFitness()
        return bestIndividual

    def populationalEvolution(self, pRegMut, pMicro, pMacro, pConst, pCrossover, numberOfVariable, numberOfInput, numberOfOperation,
                         numberOfConstant, register, pInsert, maxProgLength, minProgLength,
                         X_train, y_train, fitnessThreshold, showGenerationStat, randomSampling):
        '''
        traditional genetic evolution
        '''
        g = 0
        randomSamplingSize = "No random sampling"
        self.p.evaluatePopulation(numberOfVariable, register, X_train, y_train)
        bestIndividual = self.p.getBestIndividual()

        while g < self.maxGeneration:
            child_p = Population()

            while len(child_p.population) < len(self.p.population):
                #print(len(child_p.population))

                # Perform two fitness tournaments
                parent1, parent2 = self.twoTournamentSelectionReturnProgram()

                # Modify the two winners by one or more variation operators with certain probabilities(cross over)
                child1 = parent1
                child2 = parent2
                if np.random.random_sample() < pCrossover:
                    child1, child2 = GeneticOperations.simpleCrossover(child1, child2)
                # Mutation
                if np.random.random_sample() < pMacro:
                    randomInstr = Instruction(numberOfOperation, numberOfVariable, numberOfInput, numberOfConstant, pConst)
                    GeneticOperations.macroMutation(child1, pInsert, maxProgLength, minProgLength, randomInstr)
                if np.random.random_sample() < pMacro:
                    randomInstr = Instruction(numberOfOperation, numberOfVariable, numberOfInput, numberOfConstant, pConst)
                    GeneticOperations.macroMutation(child2, pInsert, maxProgLength, minProgLength, randomInstr)
                if np.random.random_sample() < pMicro:
                    GeneticOperations.microMutation(child1, pRegMut, pConst, numberOfVariable, numberOfInput, numberOfOperation, numberOfConstant)
                if np.random.random_sample() < pMicro:
                    GeneticOperations.microMutation(child2, pRegMut, pConst, numberOfVariable, numberOfInput, numberOfOperation, numberOfConstant)
                child_p.population.append(child1)
                child_p.population.append(child2)

            # Random Sampling Technique
            if randomSampling:
                # subset need to have a least one row
                ranIndex1, ranIndex2 = np.random.choice(X_train.shape[0], 2, replace=False)
                randomSamplingSize = abs(ranIndex1 - ranIndex2)
                if ranIndex1 < ranIndex2:
                    X_subset = X_train[ranIndex1:ranIndex2, :]
                    y_subset = y_train[ranIndex1:ranIndex2]
                else:
                    X_subset = X_train[ranIndex2:ranIndex1, :]
                    y_subset = y_train[ranIndex2:ranIndex1]
                child_p.evaluatePopulation(numberOfVariable, register, X_subset, y_subset)
            else:
                child_p.evaluatePopulation(numberOfVariable, register, X_train, y_train)

            self.p = child_p  # offspring replace parent population
            bestIndividual = self.p.getBestIndividual()
            if showGenerationStat:
                self.displayStatistics(g, bestIndividual, randomSamplingSize)

            if not randomSampling:
            # if the solution has been found, end the loop
                if bestIndividual.fitness >= fitnessThreshold:
                    return bestIndividual

            g += 1
        return bestIndividual


